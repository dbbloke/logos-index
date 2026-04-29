from state_trigger import build_history_from_session


def test_build_history_from_session_reconstructs_turns():
    session = {
        "log": [
            {"user_message": "Hello", "response": "Hi"},
            {"user_message": "How are you?", "response": "Doing well."},
        ]
    }

    history = build_history_from_session(session)

    assert history == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "Doing well."},
    ]
