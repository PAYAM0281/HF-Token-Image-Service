import reflex as rx


class HuggingFaceTokenState(rx.State):
    token: str = rx.LocalStorage(name="hf_token")