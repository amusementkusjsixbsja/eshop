import uuid

_conversations: dict[str, list[dict]] = {}

def create_conversation(user_id: int) -> str:
    conv_id = str(uuid.uuid4())
    _conversations[conv_id] = []
    return conv_id

def add_message(conv_id: str, role: str, content: str):
    if conv_id not in _conversations:
        _conversations[conv_id] = []
    _conversations[conv_id].append({"role": role, "content": content})

def get_history(conv_id: str) -> list[dict]:
    return _conversations.get(conv_id, [])


if __name__ == "__main__":
    cid = create_conversation(1)
    add_message(cid, "user", "你好")
    add_message(cid, "assistant", "你好！有什么可以帮助您的？")
    print("历史:", get_history(cid))