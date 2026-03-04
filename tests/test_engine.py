from dockfleet.core.orchestrator import Orchestrator


def test_create_when_empty_state():
    desired = {
        "services": {
            "nginx": {"image": "nginx:latest"}
        }
    }

    state = {}

    orchestrator = Orchestrator()
    plan = orchestrator.ps(desired, state)

    assert len(plan.to_create) == 1
    assert plan.to_create[0]["name"] == "nginx"
    assert len(plan.to_remove) == 0

def test_update_when_image_changes():
    desired = {
        "services": {
            "nginx": {"image": "nginx:1.25"}
        }
    }

    state = {
        "services": {
            "nginx": {"image": "nginx:latest"}
        }
    }

    orchestrator = Orchestrator()
    plan = orchestrator.ps(desired, state)

    assert len(plan.to_update) == 1

def test_no_changes_when_states_match():
    desired = {
        "services": {
            "nginx": {"image": "nginx:latest"}
        }
    }

    state = {
        "services": {
            "nginx": {"image": "nginx:latest"}
        }
    }

    orchestrator = Orchestrator()
    plan = orchestrator.ps(desired, state)

    assert plan.to_create == []
    assert plan.to_remove == []
    assert plan.to_update == []