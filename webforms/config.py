from dynaconf import Dynaconf, Validator

settings = Dynaconf(
    validators=[
        # Ensure some parameters exists (are required)
        Validator(
            'us_visa.email',
            'us_visa.password',
            'us_visa.schedule',
            'us_visa.country_code',
            'us_visa.facility_id',
            'us_visa.scheduled_date',
            'us_visa.book_date', must_exist=True), ],
        envvar_prefix="DYNACONF",
    environments=True,
    settings_files=['settings.yaml', '.secrets.yaml'],
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
