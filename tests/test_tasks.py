from app.models import TaskStatus


def test_create_task_valid_returns_201_with_full_body(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Write API tests",
            "description": "Add pytest coverage for task creation",
            "priority": "Medium",
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
    client.post("/tasks", json={"title": "low task", "priority": "Low"})
    client.post("/tasks", json={"title": "high task", "priority": "High"})

    response = client.get("/tasks", params={"priority": "High"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "high task"


def test_create_task_with_due_date_returns_it_in_response(client):
    response = client.post(
        "/tasks",
        json={
            "title": "due task",
            "priority": "Low",
            "due_date": "2099-12-31",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["due_date"] == "2099-12-31"
    assert body["is_overdue"] is False


def test_create_task_with_tags_returns_them_in_response(client):
    response = client.post(
        "/tasks",
        json={
            "title": "tagged task",
            "priority": "Medium",
            "tags": [" urgent ", "Frontend"],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tags"] == ["urgent", "Frontend"]


def test_create_task_with_invalid_tags_returns_422(client):
    response = client.post(
        "/tasks",
        json={
            "title": "bad tags",
            "priority": "Low",
            "tags": [" ", "valid"],
        },
    )

    assert response.status_code == 422


def test_create_task_with_duplicate_tags_returns_422(client):
    response = client.post(
        "/tasks",
        json={
            "title": "duplicate tags",
            "priority": "Low",
            "tags": ["urgent", "Urgent"],
        },
    )

    assert response.status_code == 422


def test_create_task_with_too_many_tags_returns_422(client):
    response = client.post(
        "/tasks",
        json={
            "title": "too many tags",
            "priority": "Low",
            "tags": [f"tag{i}" for i in range(11)],
        },
    )

    assert response.status_code == 422


def test_create_task_with_long_tag_returns_422(client):
    response = client.post(
        "/tasks",
        json={
            "title": "long tag",
            "priority": "Low",
            "tags": ["a" * 51],
        },
    )

    assert response.status_code == 422


def test_patch_tags_replaces_existing_tags(client, created_task):
    client.patch(f"/tasks/{created_task['id']}", json={"tags": ["first"]})

    response = client.patch(
        f"/tasks/{created_task['id']}",
        json={"tags": ["second"]},
    )

    assert response.status_code == 200
    assert response.json()["tags"] == ["second"]


def test_patch_without_tags_leaves_existing_tags_untouched(client):
    created = client.post(
        "/tasks",
        json={"title": "keep tags", "priority": "Medium", "tags": ["keep"]},
    )
    task_id = created.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"title": "updated title"},
    )

    assert response.status_code == 200
    assert response.json()["tags"] == ["keep"]


def test_list_tasks_filter_by_tag_returns_only_matches(client):
    client.post(
        "/tasks",
        json={"title": "urgent task", "priority": "Low", "tags": ["urgent"]},
    )
    client.post(
        "/tasks",
        json={"title": "normal task", "priority": "Low", "tags": ["other"]},
    )

    response = client.get("/tasks", params={"tag": "urgent"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "urgent task"


def test_create_task_with_malformed_due_date_returns_422(client):
    response = client.post(
        "/tasks",
        json={
            "title": "invalid due date",
            "priority": "low",
            "due_date": "not-a-date",
        },
    )

    assert response.status_code == 422


def test_create_task_with_past_due_date_and_nondone_status_is_overdue_true(client):
    response = client.post(
        "/tasks",
        json={
            "title": "overdue task",
            "priority": "High",
            "status": TaskStatus.IN_PROGRESS.value,
            "due_date": "2000-01-01",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["due_date"] == "2000-01-01"
    assert body["status"] == TaskStatus.IN_PROGRESS.value
    assert body["is_overdue"] is True


def test_create_task_with_past_due_date_and_done_status_is_overdue_false(client):
    response = client.post(
        "/tasks",
        json={
            "title": "completed overdue task",
            "priority": "High",
            "status": TaskStatus.DONE.value,
            "due_date": "2000-01-01",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["due_date"] == "2000-01-01"
    assert body["status"] == TaskStatus.DONE.value
    assert body["is_overdue"] is False


def test_list_tasks_overdue_filter_returns_only_overdue(client):
    response1 = client.post(
        "/tasks",
        json={"title": "past task", "priority": "Low", "due_date": "2000-01-01"},
    )
    response2 = client.post(
        "/tasks",
        json={"title": "future task", "priority": "Low", "due_date": "2099-01-01"},
    )
    response3 = client.post(
        "/tasks",
        json={"title": "done past task", "priority": "Low", "status": "Done", "due_date": "2000-01-01"},
    )

    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response3.status_code == 201

    response = client.get("/tasks", params={"overdue": "true"})

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "past task"
    assert tasks[0]["is_overdue"] is True


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
