"""Optional browser acceptance: explicit upgrade, v2/v3 restore, controls and portable report."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from editor_v03 import make_server
from render_v03 import export
from state_v03 import ROOT, StateStore, migrate
import state_v02

def run(browser_path,screenshot_dir):
    from playwright.sync_api import sync_playwright, expect
    with tempfile.TemporaryDirectory() as tmp:
        db=Path(tmp)/'test.sqlite';store=StateStore(db)
        p=json.loads((ROOT/'example.json').read_text());store.save(p,0,'synthetic')
        old=state_v02.migrate(p,1);store.state_save(old,0,'v2')
        report=Path(tmp)/'report';export(migrate(old,1),2,report,old);store.close()
        server=make_server(str(db),p['dog_id'],0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,executable_path=browser_path,args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1440,'height':1100});errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                expect(page.locator('#upgrade')).to_be_visible()
                page.locator('#number-ear_length').fill('26')
                expect(page.locator('#status')).to_contain_text('미리보기 갱신 완료')
                page.locator('#upgrade').click()
                expect(page.locator('#status')).to_contain_text('먼저 저장')
                expect(page.locator('#revision')).to_contain_text('제작 상태 v1')
                page.locator('#reset').click()
                expect(page.locator('#status')).to_contain_text('미리보기 갱신 완료')
                page.locator('#upgrade').click()
                expect(page.locator('#revision')).to_contain_text('제작 상태 v2')
                expect(page.locator('#buildVersion')).to_have_text('0.3')
                expect(page.locator('#compareLabel')).to_have_text('0.2과 비교')
                expect(page.locator('#upgrade')).to_be_hidden()
                expect(page.locator('#grid figure')).to_have_count(4)
                for key,value in [('head_drop','8'),('shoulder_width','30'),('haunch_width','32'),('foot_spacing','20')]:
                    page.locator('#number-'+key).fill(value)
                    expect(page.locator('#status')).to_contain_text('미리보기 갱신 완료')
                page.locator('#reason').fill('browser v3 shape edits');page.locator('#save').click()
                expect(page.locator('#revision')).to_contain_text('제작 상태 v3')
                page.reload();expect(page.locator('#number-shoulder_width')).to_have_value('30')
                page.locator('#history').select_option('1');page.locator('#restore').click()
                expect(page.locator('#revision')).to_contain_text('제작 상태 v4')
                expect(page.locator('#buildVersion')).to_have_text('0.2')
                expect(page.locator('#number-shoulder_width')).to_have_count(0)
                expect(page.locator('#compareLabel')).to_have_text('0.1과 비교')
                page.locator('#history').select_option('3');page.locator('#restore').click()
                expect(page.locator('#revision')).to_contain_text('제작 상태 v5')
                expect(page.locator('#buildVersion')).to_have_text('0.3')
                expect(page.locator('#number-shoulder_width')).to_have_value('30')
                page.get_by_text('세부 치수',exact=True).click()
                page.locator('#number-foot_spacing').fill('12');page.locator('#number-leg_width').fill('13')
                expect(page.locator('#status')).to_have_class('error');expect(page.locator('#save')).to_be_disabled()
                page.locator('#reset').click();expect(page.locator('#status')).to_contain_text('미리보기 갱신 완료')
                page.locator('#compare').check();page.locator('#overlay').check()
                if screenshot_dir:
                    out=Path(screenshot_dir);out.mkdir(parents=True,exist_ok=True)
                    page.screenshot(path=str(out/'editor-desktop.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                if screenshot_dir:page.screenshot(path=str(out/'editor-mobile.png'),full_page=True)
                # The managed browser blocks file:// navigation; load the exact standalone
                # HTML contents to verify its embedded images without companion resources.
                page.set_content((report/'index.html').read_text(),wait_until='load')
                expect(page.locator('img')).to_have_count(12)
                assert page.locator('img').evaluate_all('(images)=>images.every(i=>i.complete && i.naturalWidth===96)')
                page.locator('#scale').select_option('96');page.locator('#background').click()
                expect(page.locator('body')).to_have_class('dark')
                assert page.locator('img').first.evaluate('(i)=>i.getBoundingClientRect().width')==96
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.locator('#scale').select_option('384')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert not errors,errors
                browser.close()
            store=StateStore(db)
            try:
                assert store.get(p['dog_id'])==(p,1)
                assert store.state_get(p['dog_id'])[1]==5
            finally:store.close()
            print('Browser pass: dirty upgrade blocked, explicit migration, v3 controls, save/reload, v2/v3 restore, invalid feet, mobile layout, 12 embedded report images, scale/background; no JS errors.')
        finally:server.shutdown();thread.join();server.server_close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--browser',default='/usr/bin/chromium');parser.add_argument('--screenshots')
    args=parser.parse_args();run(args.browser,args.screenshots)
