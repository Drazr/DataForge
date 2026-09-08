import json
import pytest
from product import cli


def test_fixture_failure_replaces_old_success_status(tmp_path,monkeypatch):
    monkeypatch.setattr(cli,'ROOT',tmp_path)
    monkeypatch.setattr(cli.sys,'argv',['product.cli','live'])
    async def ready():return {'sdk':'ready'},0
    async def fail():raise OSError('Fixture download failed')
    monkeypatch.setattr(cli,'preflight',ready)
    monkeypatch.setattr(cli,'fixtures',fail)
    path=tmp_path/'evidence'/'live-status.json'
    path.parent.mkdir()
    path.write_text(json.dumps({'status':'passed'}))
    with pytest.raises(SystemExit) as result:
        cli.main()
    assert result.value.code==1
    assert json.loads(path.read_text())['status']=='failed'


@pytest.mark.parametrize('stage',['preflight','fixtures','browser'])
def test_interrupted_live_run_cannot_retain_old_success(tmp_path,monkeypatch,stage):
    monkeypatch.setattr(cli,'ROOT',tmp_path)
    monkeypatch.setattr(cli.sys,'argv',['product.cli','live'])
    path=tmp_path/'evidence'/'live-status.json'
    path.parent.mkdir()
    path.write_text(json.dumps({'status':'passed'}))
    async def ready():
        assert json.loads(path.read_text())['status']=='running'
        if stage=='preflight':raise KeyboardInterrupt()
        return {'sdk':'ready'},0
    async def fixtures():
        if stage=='fixtures':raise KeyboardInterrupt()
    def browser(*args,**kwargs):raise KeyboardInterrupt()
    monkeypatch.setattr(cli,'preflight',ready)
    monkeypatch.setattr(cli,'fixtures',fixtures)
    monkeypatch.setattr(cli.subprocess,'call',browser)
    with pytest.raises(SystemExit) as result:
        cli.main()
    assert result.value.code==130
    report=json.loads(path.read_text())
    assert report['status']=='interrupted'
    assert report['run_id'] and report['finished_at']
