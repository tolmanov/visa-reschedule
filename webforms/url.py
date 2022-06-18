from webforms import settings


class UrlGenerator:
    def __init__(self):
        details = settings.us_visa
        self.schedule = details.schedule
        self.country_code = details.country_code  # en-ca for Canada-English
        self.facility_id = details.facility_id  # 94 for Toronto (others please use F12 to check)

    @property
    def date_url(self):
        return f"https://ais.usvisa-info.com/{self.country_code}/niv/schedule/{self.schedule}/appointment/days/{self.facility_id}.json?appointments[expedite]=false"

    @property
    def time_url(self):
        return f"https://ais.usvisa-info.com/{self.country_code}/niv/schedule/{self.schedule}/appointment/times/{self.facility_id}.json?date=%s&appointments[expedite]=false"

    @property
    def appointment_url(self):
        return f"https://ais.usvisa-info.com/{self.country_code}/niv/schedule/{self.schedule}/appointment"
