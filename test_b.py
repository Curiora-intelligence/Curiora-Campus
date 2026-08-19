from app.services.curio import CurioService
service = CurioService()
image_path = "/Users/saiganeshsattenapalli/.gemini/antigravity/brain/6cf960ba-17c2-43b5-bb95-1c3dcde8bec1/.user_uploaded/media_1786577776025.png"
print("1. Image")
_, cid = service.respond(message="What does this code do?", image_path=image_path)
print("2. Text")
ans, _ = service.respond(message="Explain the code deeply.", conversation_id=cid)
print("ANS:", ans[:500])
