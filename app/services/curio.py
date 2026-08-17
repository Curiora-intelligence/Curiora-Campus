from __future__ import annotations

from app.services.model_gateway import ModelGateway
from app.services.vision import VisionService


class CurioService:

    def __init__(self) -> None:
        self.gateway = ModelGateway()

        self.vision = VisionService(self.gateway)

    def respond(self,message: str = "",image_path: str | None = None) -> str:

        if image_path is not None:

            return self.vision.analyze(image_path=image_path,message=message)

        raise NotImplementedError("Text-only Curio is the next model integration.")