from webforms import settings
from notify_run import Notify
from webforms.visa import get_available_date

from unittest.mock import patch


def test_dynaconf():
    return settings.app_name == 'webforms_test'


@patch.object(Notify, "send")
def test_get_available_date(send):
    send.return_value = True  # We don't want test to send notifications
    dates = [
        {'date': '2022-08-01', 'business_day': True}, ]
    res = get_available_date(dates)
    assert res
