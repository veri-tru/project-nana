"""Check recorded review evidence; this does not judge image quality."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def check(path):
    errors=[]
    try:
        data=json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError) as exc:
        return [f'Cannot read review status: {exc}']
    if not isinstance(data,dict):return ['Review status must be an object']
    if data.get('schema_version')!=1:errors.append('Unsupported or missing schema_version')
    artifacts=data.get('artifacts',[])
    if not isinstance(artifacts,list) or not artifacts:
        return errors+['No reviewed artifacts']
    expected={}
    for artifact in artifacts:
        if not isinstance(artifact,dict):errors.append('Invalid artifact entry');continue
        name,digest=artifact.get('path'),artifact.get('sha256')
        if not isinstance(name,str) or not name or not isinstance(digest,str):
            errors.append('Missing artifact path/hash');continue
        if name in expected:errors.append(f'Duplicate artifact: {name}')
        expected[name]=digest
        target=path.parent/name
        try:actual=hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError:errors.append(f'Missing artifact: {name}');continue
        if actual!=digest:errors.append(f'Artifact changed: {name}')
    reviewers=[]
    implementer=data.get('implementer')
    if not isinstance(implementer,str) or not implementer.strip():errors.append('Missing implementer')
    inputs=data.get('inputs')
    if not isinstance(inputs,dict) or not inputs:errors.append('Missing generation input hashes');inputs={}
    for name,digest in inputs.items():
        if not isinstance(name,str) or not isinstance(digest,str):errors.append('Invalid input hash entry');continue
        try:actual=hashlib.sha256((path.parent/name).read_bytes()).hexdigest()
        except OSError:errors.append(f'Missing generation input: {name}');continue
        if actual!=digest:errors.append(f'Generation input changed: {name}')
    reviews=data.get('reviews',{})
    if not isinstance(reviews,dict):return errors+['Invalid reviews object']
    for role in ('technical','visual'):
        review=reviews.get(role,{})
        if not isinstance(review,dict):errors.append(f'{role}: invalid review');continue
        if review.get('status')!='PASS':errors.append(f'{role}: not PASS')
        reviewer=review.get('reviewer')
        if not isinstance(reviewer,str) or not reviewer.strip():errors.append(f'{role}: missing reviewer')
        else:reviewers.append(reviewer)
        if reviewer and reviewer==implementer:errors.append(f'{role}: reviewer is the implementer')
        if review.get('artifacts')!=expected:errors.append(f'{role}: artifact set/hash mismatch')
        if role=='technical' and review.get('inputs')!=inputs:errors.append('technical: input set/hash mismatch')
        if not isinstance(review.get('coverage'),list) or not review['coverage']:
            errors.append(f'{role}: missing coverage record')
        if review.get('coverage_complete') is not True:errors.append(f'{role}: incomplete review coverage')
        report=review.get('report');digest=review.get('report_sha256')
        if not isinstance(report,str) or not report or not isinstance(digest,str):
            errors.append(f'{role}: missing report/hash');continue
        try:report_bytes=(path.parent/report).read_bytes();actual=hashlib.sha256(report_bytes).hexdigest()
        except OSError:errors.append(f'{role}: missing report');continue
        if actual!=digest:errors.append(f'{role}: report changed')
        markers=re.findall(r'^<!-- review-verdict: (.+) -->\r?$',report_bytes.decode('utf-8'),re.MULTILINE)
        try:
            if len(markers)!=1:raise ValueError('exactly one verdict marker required')
            verdict=json.loads(markers[0])
            if not isinstance(verdict,dict):raise ValueError('verdict must be an object')
        except ValueError as exc:errors.append(f'{role}: invalid report verdict ({exc})');continue
        for key in ('status','reviewer','artifacts','coverage_complete'):
            if verdict.get(key)!=review.get(key):errors.append(f'{role}: report/status mismatch for {key}')
        if role=='technical' and verdict.get('inputs')!=inputs:errors.append('technical: report input hashes mismatch')
        unresolved=verdict.get('unresolved')
        if not isinstance(unresolved,dict):errors.append(f'{role}: missing report finding dispositions')
        else:
            for issue,severity in unresolved.items():
                if severity not in ('BLOCKER','MAJOR','MINOR'):errors.append(f'{role}: invalid report severity for {issue}')
                if severity in ('BLOCKER','MAJOR'):errors.append(f'{role}: report has unresolved {severity} {issue}')
    if len(reviewers)==2 and reviewers[0]==reviewers[1]:errors.append('Review roles must have separate reviewers')
    findings=data.get('findings')
    if not isinstance(findings,list):errors.append('Missing findings record')
    else:
        for finding in findings:
            if not isinstance(finding,dict):errors.append('Invalid finding');continue
            if finding.get('severity') not in ('BLOCKER','MAJOR','MINOR'):
                errors.append(f'Invalid severity: {finding.get("id")}')
            if finding.get('severity') in ('BLOCKER','MAJOR') and finding.get('resolved') is not True:
                errors.append(f'Unresolved {finding["severity"]}: {finding.get("id")}')
    if data.get('user_decision') not in ('PENDING','ACCEPTED','REJECTED'):
        errors.append('Missing or invalid user_decision')
    if data.get('user_decision')=='REJECTED':errors.append('User rejected this candidate')
    history=data.get('history',[])
    if not isinstance(history,list):errors.append('Invalid decision history')
    else:
        decisions=[event for event in history if isinstance(event,dict) and event.get('artifacts')==expected and event.get('event') in ('USER_REJECTED','USER_ACCEPTED')]
        if decisions:
            latest=decisions[-1]['event']
            if latest=='USER_REJECTED':errors.append('Latest recorded user decision rejects these image hashes')
            expected_decision='REJECTED' if latest=='USER_REJECTED' else 'ACCEPTED'
            if data.get('user_decision')!=expected_decision:errors.append('User decision contradicts recorded history')
    if data.get('delivery')!='READY':errors.append('Delivery is not READY')
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('status',type=Path)
    args=parser.parse_args()
    errors=check(args.status.resolve())
    print(json.dumps(dict(delivery='BLOCKED' if errors else 'READY',reasons=errors),ensure_ascii=False,indent=2))
    raise SystemExit(1 if errors else 0)


if __name__=='__main__':main()
