import time

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Debugging
from aiosmtpd.smtp import AuthResult


def accept_any_auth(server, session, envelope, mechanism, auth_data):
    return AuthResult(success=True)


if __name__ == '__main__':
    controller = Controller(
        Debugging(),
        hostname='localhost',
        port=25,
        auth_required=True,
        auth_require_tls=False,
        authenticator=accept_any_auth,
    )
    controller.start()
    print('Dev SMTP catcher running on localhost:25 (Ctrl+C to stop)')
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
