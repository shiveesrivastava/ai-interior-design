import io
from PIL import Image
from utils.logger import get_logger

logger = get_logger("ml_service")

pipe = None
depth_estimator = None

def load_pipeline():
    global pipe, depth_estimator

    try:
        import torch
        if not torch.cuda.is_available():
            logger.warning("CUDA not available — dummy mode active")
            return
    except ImportError:
        logger.warning("torch not installed — dummy mode active")
        return

    logger.info("CUDA detected — loading ML pipeline...")

    from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
    from diffusers import UniPCMultistepScheduler
    from transformers import pipeline as hf_pipeline

    import torch

    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/sd-controlnet-depth",
        torch_dtype=torch.float16
    )

    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        controlnet=controlnet,
        torch_dtype=torch.float16
    ).to("cuda")

    pipe.scheduler = UniPCMultistepScheduler.from_config(
        pipe.scheduler.config
    )
    pipe.enable_model_cpu_offload()
    pipe.enable_attention_slicing()

    depth_estimator = hf_pipeline(
        "depth-estimation",
        model="LiheYoung/depth-anything-base-hf"
    )

    logger.info("ML pipeline loaded successfully")


def generate(image_bytes: bytes, style: str = "scandinavian") -> bytes:
    logger.info(f"ML service called | style: {style}")

    input_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    input_image = input_image.resize((512, 512))

    if pipe is None or depth_estimator is None:
        logger.warning("Pipeline not loaded — returning input image (dummy mode)")
        return image_bytes

    style_prompts = {
        "scandinavian": "a modern scandinavian living room, warm lighting, minimalist furniture, hardwood floors, photorealistic, interior design magazine, 8k",
        "royal":        "a luxurious royal living room, gold accents, velvet furniture, photorealistic",
        "industrial":   "an industrial loft, exposed brick walls, metal fixtures, photorealistic",
        "bohemian":     "a bohemian cozy room, warm earth tones, plants everywhere, photorealistic"
    }

    prompt = style_prompts.get(style, style_prompts["scandinavian"])
    negative_prompt = "ugly, blurry, bad proportions, unrealistic, cartoon, drawing, dark, gloomy"

    logger.info("Running depth estimation...")
    depth_result = depth_estimator(input_image)
    depth_map = depth_result["depth"].resize((512, 512))

    logger.info("Running Stable Diffusion + ControlNet...")
    import torch
    result_image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        image=depth_map,
        num_inference_steps=20,
        guidance_scale=7.5
    ).images[0]

    output = io.BytesIO()
    result_image.save(output, format="JPEG", quality=95)
    logger.info("Generation complete")

    return output.getvalue()