import reflex as rx
from app.states.generate import ImageGenState
from app.states.token import HuggingFaceTokenState


def param_slider(
    name: str,
    default: int | float,
    min_val: int,
    max_val: int,
    step: int | float,
    on_change,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                name.replace("_", " ").title(),
                class_name="text-sm font-medium text-gray-700",
            ),
            rx.el.span(
                getattr(ImageGenState, name), class_name="text-sm font-semibold"
            ),
            class_name="flex justify-between items-center",
        ),
        rx.el.input(
            type_="range",
            default_value=default,
            min=min_val,
            max=max_val,
            step=step,
            on_change=lambda val: on_change(val),
            class_name="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700",
        ),
        class_name="space-y-2",
    )


def index() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Image Generation",
                    class_name="text-2xl font-bold tracking-tight text-gray-900",
                ),
                rx.el.p(
                    "Generate images with Stable Diffusion.", class_name="text-gray-600"
                ),
                class_name="flex-grow",
            ),
            rx.el.div(
                rx.icon("settings", class_name="text-gray-600"),
                class_name="p-2 rounded-md hover:bg-gray-100 cursor-pointer",
            ),
            class_name="flex items-center justify-between p-4 border-b",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h2("Generated Image", class_name="text-lg font-semibold"),
                    rx.el.div(
                        rx.el.div(
                            rx.cond(
                                ImageGenState.is_generating,
                                rx.el.div(
                                    rx.el.div(
                                        class_name="w-full h-full bg-gray-200 animate-pulse rounded-lg"
                                    ),
                                    rx.el.div(
                                        rx.el.div(
                                            rx.el.div(
                                                style={
                                                    "width": ImageGenState.progress_percent_str
                                                },
                                                class_name="bg-blue-600 h-2 rounded-full",
                                            ),
                                            class_name="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700",
                                        ),
                                        rx.el.p(f"{ImageGenState.progress * 100:.0f}%"),
                                        class_name="w-full flex items-center gap-2",
                                    ),
                                    class_name="flex flex-col items-center justify-center w-full h-full gap-4",
                                ),
                                rx.image(
                                    src=ImageGenState.generated_image,
                                    class_name="rounded-lg object-contain aspect-square w-full",
                                ),
                            ),
                            class_name="relative w-full h-full min-h-[512px] flex items-center justify-center bg-gray-50 rounded-lg border border-dashed",
                        ),
                        class_name="p-4 bg-white rounded-lg shadow-sm",
                    ),
                    class_name="space-y-4",
                ),
                class_name="col-span-2 space-y-4",
            ),
            rx.el.div(
                rx.el.form(
                    rx.el.h2("Generation Settings", class_name="text-lg font-semibold"),
                    rx.el.div(
                        rx.el.label(
                            "Model", class_name="text-sm font-medium text-gray-700"
                        ),
                        rx.el.select(
                            rx.foreach(
                                ImageGenState.available_models,
                                lambda model: rx.el.option(model, value=model),
                            ),
                            value=ImageGenState.model_id,
                            on_change=ImageGenState.set_model_id,
                            class_name="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md",
                        ),
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Prompt", class_name="text-sm font-medium text-gray-700"
                        ),
                        rx.el.textarea(
                            default_value=ImageGenState.prompt,
                            on_change=ImageGenState.set_prompt,
                            placeholder="A beautiful landscape painting...",
                            class_name="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                        ),
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Negative Prompt",
                            class_name="text-sm font-medium text-gray-700",
                        ),
                        rx.el.textarea(
                            default_value=ImageGenState.negative_prompt,
                            on_change=ImageGenState.set_negative_prompt,
                            placeholder="ugly, tiling, poorly drawn...",
                            class_name="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm",
                        ),
                    ),
                    param_slider(
                        "num_inference_steps",
                        25,
                        1,
                        100,
                        1,
                        ImageGenState.set_num_inference_steps,
                    ),
                    param_slider(
                        "guidance_scale",
                        7.5,
                        1.0,
                        20.0,
                        0.1,
                        ImageGenState.set_guidance_scale,
                    ),
                    param_slider("width", 1024, 512, 1024, 8, ImageGenState.set_width),
                    param_slider(
                        "height", 1024, 512, 1024, 8, ImageGenState.set_height
                    ),
                    rx.el.div(
                        rx.el.label(
                            "LoRA", class_name="text-sm font-medium text-gray-700"
                        ),
                        rx.el.select(
                            rx.foreach(
                                ImageGenState.available_loras,
                                lambda lora: rx.el.option(lora, value=lora),
                            ),
                            value=ImageGenState.lora_path,
                            on_change=ImageGenState.set_lora_path,
                            class_name="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md",
                        ),
                    ),
                    rx.cond(
                        ImageGenState.lora_path != "",
                        param_slider(
                            "lora_scale",
                            0.8,
                            0.0,
                            2.0,
                            0.1,
                            ImageGenState.set_lora_scale,
                        ),
                        None,
                    ),
                    rx.el.button(
                        rx.cond(
                            ImageGenState.is_generating,
                            "Generating...",
                            "Generate Image",
                        ),
                        type_="submit",
                        disabled=ImageGenState.is_generating,
                        class_name="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50",
                    ),
                    on_submit=ImageGenState.start_generation,
                    class_name="space-y-4",
                ),
                class_name="col-span-1 p-4 bg-white rounded-lg shadow-sm h-fit",
            ),
            class_name="grid grid-cols-1 lg:grid-cols-3 gap-6 p-4",
        ),
        class_name="h-screen w-screen bg-gray-50 font-sans",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[rx.el.script(src="/js/main.js")],
)
app.add_page(
    index,
    on_load=[
        ImageGenState.on_generation_start,
        ImageGenState.on_generation_progress,
        ImageGenState.on_generation_result,
        ImageGenState.on_generation_error,
        ImageGenState.get_available_loras,
    ],
)