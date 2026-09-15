"""Provider grouping without changing existing TTS method/config identifiers."""

PROVIDERS = {
    "302.ai": ("azure_tts", "openai_tts", "fish_tts", "f5tts"),
    "SiliconFlow": ("sf_fish_tts", "sf_cosyvoice2"),
    "Microsoft Edge": ("edge_tts",),
    "Local service": ("gpt_sovits",),
    "Custom provider": ("custom_tts",),
}
KEY_PATHS = {
    "302.ai": ("azure_tts.api_key", "openai_tts.api_key", "fish_tts.api_key", "f5tts.302_api"),
    "SiliconFlow": ("sf_fish_tts.api_key", "sf_cosyvoice2.api_key"),
}


def configured_keys(provider, method, load_key):
    """Prefer the selected method; reuse a sole existing key without writing it."""
    paths = KEY_PATHS[provider]
    values = {path: load_key(path) for path in paths}
    usable = {path: value for path, value in values.items()
              if value and not value.startswith("YOUR_")}
    current = paths[PROVIDERS[provider].index(method)]
    conflict = len(set(usable.values())) > 1
    value = usable.get(current, "" if conflict else next(iter(usable.values()), ""))
    return value, conflict


def save_provider_key(provider, value):
    """Update legacy fields together; never migrate credentials on page render."""
    from core.utils import config_utils

    with config_utils.lock:
        with open(config_utils.CONFIG_PATH, encoding="utf-8") as file:
            data = config_utils.yaml.load(file)
        for path in KEY_PATHS[provider]:
            section, key = path.split(".")
            data[section][key] = value
        with open(config_utils.CONFIG_PATH, "w", encoding="utf-8") as file:
            config_utils.yaml.dump(data, file)


def select_tts_method(labels):
    import streamlit as st
    from translations.translations import translate as t
    from core.utils.config_utils import load_key, update_key

    current = load_key("tts_method")
    provider = next((name for name, methods in PROVIDERS.items() if current in methods), None)
    chosen = st.selectbox(t("TTS Provider"), list(PROVIDERS),
                          index=list(PROVIDERS).index(provider) if provider else None,
                          format_func=lambda name: t(name))
    if chosen is None:
        return None
    methods = PROVIDERS[chosen]
    selected = st.selectbox(t("TTS Method"), methods,
                            index=methods.index(current) if current in methods else None,
                            format_func=lambda method: labels[method])
    if selected is None:
        return None
    if selected != current:
        update_key("tts_method", selected)
        st.rerun()
    if chosen in KEY_PATHS:
        value, conflict = configured_keys(chosen, selected, load_key)
        if conflict:
            st.warning(t("Existing methods use different keys. Editing this field replaces all keys for this provider."))
        entered = st.text_input(t("Provider API Key"), value=value, type="password",
                                help=t("Shared by all TTS methods under this provider."))
        if entered != value:
            save_provider_key(chosen, entered)
            st.rerun()
        # A sole legacy key is shown for convenience, but only saving propagates it.
        if value and any(load_key(p) != value for p in KEY_PATHS[chosen]):
            if st.button(t("Use this key for all methods"), key=f"tts_share_{chosen}"):
                save_provider_key(chosen, value)
                st.rerun()
    return selected
