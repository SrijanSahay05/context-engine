from core.config import Settings
from db.session import DatabaseSessionManager
from services.conversation import list_conversations, create_conversation, send_message


def main() -> None:
    settings: Settings = Settings()
    db: DatabaseSessionManager = DatabaseSessionManager(settings.database_url)

    try:
        # 1. Give option for new conversation / resume conversation

        print("Press '1' to start a new conversation and '2' to resume a conversation.")
        user_input = input(">>> ")
        match user_input:
            case "1":
                conversation_id = create_conversation(db=db)
            case "2":
                conversations = list_conversations(db=db)
                if len(conversations) == 0:
                    print(
                        "No conversations found. Starting a new conversation instead."
                    )
                    conversation_id = create_conversation(db=db)
                else:
                    print("Available Conversations:")
                    for conversation in conversations:
                        print(conversation)
                    conversation_id = int(
                        input("Enter the conversation ID you want to resume: ")
                    )
            case _:
                print("Invalid input. Please try again.")
                return

        print("/exit to exit the chat.")
        while True:
            user_message = input("You: ")
            if user_message == "/exit":
                break
            ai_response = send_message(
                db=db, conversation_id=conversation_id, user_message=user_message
            )
            print("AI:", ai_response)
            print("\n")
    finally:
        db.dispose()


if __name__ == "__main__":
    main()
