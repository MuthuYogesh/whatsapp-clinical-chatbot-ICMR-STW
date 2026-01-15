from app.state_store.store import (
    get_state,
    set_state,
    clear_state,
    reset_store,
)


def test_set_and_get_state():
    reset_store()

    sender_id = "919999999999"
    state = {
        "stage": "AWAITING_CLARIFICATION",
        "stw": "ENT_Acute_Rhinosinusitis",
        "clinical_facts": {
            "duration_days": None,
            "nasal_discharge_type": None,
            "red_flags_present": None
        }
    }

    set_state(sender_id, state)
    stored = get_state(sender_id)

    assert stored is not None
    assert stored["stage"] == "AWAITING_CLARIFICATION"
    assert stored["stw"] == "ENT_Acute_Rhinosinusitis"


def test_clear_state():
    reset_store()

    sender_id = "919888888888"
    set_state(sender_id, {"stage": "NEW"})

    clear_state(sender_id)

    assert get_state(sender_id) is None


def test_clear_non_existing_state():
    reset_store()

    # should not raise error
    clear_state("non_existing_user")

    assert True


def test_reset_store():
    set_state("user1", {"stage": "NEW"})
    set_state("user2", {"stage": "DONE"})

    reset_store()

    assert get_state("user1") is None
    assert get_state("user2") is None
