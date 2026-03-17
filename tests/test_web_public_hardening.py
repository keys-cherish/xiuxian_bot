import web_public.app as public_app


def test_public_index_hides_admin_panel_entry():
    client = public_app.app.test_client()
    resp = client.get("/")
    html = resp.get_data(as_text=True)

    assert resp.status_code == 200
    assert "复制管理面板地址" not in html
    assert "data-action=\"copy-admin\"" not in html
    assert "<span>管理面板</span>" not in html
