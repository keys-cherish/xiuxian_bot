import os
import logging
import datetime
from flask import Flask, render_template, jsonify

from core.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "web_public.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WebPublic")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, 'static'),
    template_folder=os.path.join(BASE_DIR, 'templates'),
)


def load_config():
    """兼容函数：返回统一配置的 raw dict。"""
    return config.raw


@app.route("/")
def index():
    public_cfg = config.get("public_web", {}) or {}
    port = int(public_cfg.get("port", 11452))
    return render_template(
        "index.html",
        core_port=config.core_server_port,
        public_port=port,
        core_version=os.getenv("CORE_VERSION", "dev"),
        web_version=os.getenv("WEB_VERSION", "dev"),
        telegram_version=os.getenv("TELEGRAM_VERSION", "dev"),
        year=datetime.datetime.now().year,
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    cfg = load_config()
    public_cfg = cfg.get("public_web", {}) if isinstance(cfg, dict) else {}
    port = int(public_cfg.get("port", 11452))
    host = str(public_cfg.get("host", "127.0.0.1"))
    logger.info("Starting web_public on http://%s:%s", host, port)
    app.run(host=host, port=port, debug=False)
