from app.models import TaskStatus


def test_create_task_valid_returns_201_with_full_body(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Write API tests",
            "description": "Add pytest coverage for task creation",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Write API tests"
    assert body["description"] == "Add pytest coverage for task creation"
    assert body["status"] == TaskStatus.TODO.value
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


def test_create_task_missing_title_returns_422(client):
    response = client.post("/tasks", json={"description": "missing title"})

    assert response.status_code == 422


def test_create_task_blank_title_returns_422(client):
    response = client.post("/tasks", json={"title": "   "})

    assert response.status_code == 422


def test_create_task_invalid_priority_returns_422(client):
    response = client.post("/tasks", json={"title": "bad priority", "priority": "urgent"})

    assert response.status_code == 422


def test_create_task_unknown_field_returns_422(client):
    response = client.post("/tasks", json={"title": "unknown field", "unexpected": True})

    assert response.status_code == 422


def test_list_tasks_empty_returns_200_and_empty_list(client):
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_status_no_match_returns_200_and_empty_list(client):
    client.post("/tasks", json={"title": "first task"})

    response = client.get("/tasks", params={"status": TaskStatus.IN_PROGRESS.value})

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_priority_returns_only_matches(client):
    client.post("/tasks", json={"title": "low task", "priority": "low"})
    client.post("/tasks", json={"title": "high task", "priority": "high"})

    response = client.get("/tasks", params={"priority": "high"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "high task"


def test_get_task_by_id_returns_task(client, created_task):
    response = client.get(f"/tasks/{created_task['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created_task["id"]
    assert body["title"] == "fixture task"
    assert body["status"] == TaskStatus.TODO.value


def test_get_task_by_id_not_found_returns_404_with_detail(client):
    response = client.get("/tasks/not-a-real-id")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task with id not-a-real-id not found"}


def test_patch_partial_update_keeps_other_fields(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"title": "updated title"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "updated title"
    assert body["description"] is None
    assert body["status"] == TaskStatus.TODO.value


def test_patch_not_found_returns_404(client):
    response = client.patch("/tasks/not-a-real-id", json={"title": "updated title"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Task with id not-a-real-id not found"}


def test_patch_valid_transition_todo_to_inprogress_returns_200(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"status": TaskStatus.IN_PROGRESS.value},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == TaskStatus.IN_PROGRESS.value


def test_patch_invalid_transition_todo_to_done_returns_422(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"status": TaskStatus.DONE.value},
    )

    assert response.status_code == 422


def test_patch_same_status_returns_422(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"status": TaskStatus.TODO.value},
    )

    assert response.status_code == 422


def test_patch_invalid_transition_inprogress_to_todo_returns_422(client):
    created_response = client.post(
        "/tasks",
        json={
            "title": "Reopen task",
            "priority": "Low",
            "status": TaskStatus.IN_PROGRESS.value,
        },
    )
    assert created_response.status_code == 201

    response = client.patch(
        f"/tasks/{created_response.json()['id']}",
        json={"status": TaskStatus.TODO.value},
    )

    assert response.status_code == 422


def test_delete_existing_returns_204_no_body(client, created_task):
    response = client.delete(f"/tasks/{created_task['id']}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_returns_404(client):
    response = client.delete("/tasks/not-a-real-id")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task with id not-a-real-id not found"}
