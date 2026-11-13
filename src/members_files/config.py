"""Config for Phoenix Members Files."""

from psiconfig import ConfigField, TomlConfig

from members_files.constants import CONFIG_PATH

# FIELDS for config, and to create tkinter variables in frm_config.py
# e.g. self.data_directory is a tk.StringVar
FIELDS = {
    "members_file": ConfigField(str, ""),
    "include_list_file": ConfigField(str, ""),
    "bbo_names_file": ConfigField(str, ""),
}

DEFAULT_CONFIG = {}
for name, field in FIELDS.items():
    DEFAULT_CONFIG[name] = field.default_value


def read_config(restore_defaults: bool = False) -> TomlConfig:
    """Return the config file."""
    return TomlConfig(
        path=CONFIG_PATH,
        defaults=DEFAULT_CONFIG,
        restore_defaults=restore_defaults,
    )


def save_config(config: TomlConfig) -> TomlConfig | None:
    result = config.save()
    if result != config.STATUS_OK:
        return None
    config = TomlConfig(CONFIG_PATH)
    return config


config = read_config()
