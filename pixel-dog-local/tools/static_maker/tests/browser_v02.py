"""Optional UI acceptance check: requires Playwright and a Chromium executable."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from editor_v02 import make_server
from state_v02 import ROOT, StateStore, migrate

def run(browser_path,screenshot_dir):
    from playwright.sync_api import sync_playwright, expect
    with tempfile.TemporaryDirectory() as tmp:
        db=Path(tmp)/'browser.sqlite';store=StateStore(db)
        p=json.loads((ROOT/'example.json').read_text());store.save(p,0,'browser fixture')
        store.state_save(migrate(p,1),0,'migration');store.close()
        server=make_server(str(db),p['dog_id'],0)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(headless=True,executable_path=browser_path,args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1440,'height':1100});errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                expect(page.locator('#grid figure')).to_have_count(4)
                expect(page.locator('#revision')).to_contain_text('제작 상태 v1')
                page.locator('#compare').check();page.locator('#overlay').check()
                expect(page.locator('body')).to_have_class('compare overlay-on')
                page.locator('#number-ear_length').fill('26')
                expect(page.locator('#status')).to_contain_text('미리보기 갱신 완료')
                page.locator('#reason').fill('browser ear change');page.locator('#save').click()
                expect(page.locator('#revision')).to_contain_text('제작 상태 v2')
                page.reload();expect(page.locator('#number-ear_length')).to_have_value('26')
                page.locator('#history').select_option('1');page.locator('#restore').click()
                expect(page.locator('#revision')).to_contain_text('제작 상태 v3')
                expect(page.locator('#number-ear_length')).to_have_value('24')
                page.get_by_text('세부 치수',exact=True).click()
                page.locator('#number-muzzle_height').fill('10');page.locator('#number-nose_height').fill('7')
                expect(page.locator('#status')).to_have_class('error')
                expect(page.locator('#save')).to_be_disabled()
                page.locator('#reset').click()
                expect(page.locator('#status')).to_contain_text('미리보기 갱신 완료')
                expect(page.locator('#save')).to_be_enabled()
                page.locator('#compare').check();page.locator('#overlay').check()
                if screenshot_dir:
                    out=Path(screenshot_dir);out.mkdir(parents=True,exist_ok=True)
                    page.screenshot(path=str(out/'editor-desktop.png'),full_page=True)
                    page.set_viewport_size({'width':390,'height':844})
                    page.locator('#native').check()
                    page.screenshot(path=str(out/'editor-mobile.png'),full_page=True)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert not errors,errors
                browser.close()
            store=StateStore(db)
            try:
                assert store.get(p['dog_id'])==(p,1)
                assert store.state_get(p['dog_id'])[1]==3
            finally:store.close()
            print('Browser pass: load, 4 views, controls, overlays, save, reload, restore, invalid combination, reset, responsive layout; no page errors.')
        finally:server.shutdown();thread.join();server.server_close()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--browser',default='/usr/bin/chromium');ap.add_argument('--screenshots')
    args=ap.parse_args();run(args.browser,args.screenshots)
