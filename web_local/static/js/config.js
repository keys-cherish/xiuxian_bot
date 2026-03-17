document.getElementById('save-btn').addEventListener('click', async () => {
  try {
    const updated = editor.get();
    const params = new URLSearchParams(window.location.search);
    const lang   = params.get('lang') || 'zh';
    const resp = await fetch(`/config?lang=${lang}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updated)
    });
    const data = await resp.json();
    if (data.status === 'ok') {
      if (data.full_restart) {
        showPopup('⚠️ ' + data.message + '\n' + '需要重启核心服务。' + '\n' + '请重启 `start.py`');
      } else if (data.adapter_restart) {
        showPopup('⚠️ ' + data.message + '\n' + '需要重启适配器。' + '\n' + '请重启受影响的平台适配器');
      } else {
        showPopup('✅ ' + data.message);
      }
    } else {
      showPopup('❌ ' + data.message);
    }
  } catch (e) {
    showPopup('保存失败：' + e);
  }
});
