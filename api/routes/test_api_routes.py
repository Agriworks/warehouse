import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime, timezone
from unittest.mock import MagicMock

from api.routes import datasets as datasets_router
from api.routes import metadata as metadata_router
from api.routes import properties as properties_router
from api.routes import rows as rows_router
from base.models.dataset import Dataset, DataRows

FIXED_DATETIME_STR = "2025-01-01T12:00:00+00:00"
FIXED_DATETIME = datetime.fromisoformat(FIXED_DATETIME_STR)


@pytest.fixture(scope="module")
def app():
    application = FastAPI()
    application.include_router(
        datasets_router.router, prefix="/datasets", tags=["datasets"]
    )
    application.include_router(
        metadata_router.router, prefix="/datasets", tags=["metadata"]
    )
    application.include_router(
        properties_router.router, prefix="/datasets", tags=["properties"]
    )
    application.include_router(rows_router.router, prefix="/datasets", tags=["rows"])
    return application


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


def create_mock_dataset_db_object(**kwargs):
    mock_dataset = MagicMock(spec=Dataset)
    mock_dataset.dataset_id = kwargs.get("dataset_id", 1)
    mock_dataset.title = kwargs.get("title", "Test Dataset")
    mock_dataset.author = kwargs.get("author", "test_author")
    mock_dataset.column_labels = kwargs.get("column_labels", ["col1", "col2"])
    mock_dataset.is_public = kwargs.get("is_public", True)
    mock_dataset.date_created = kwargs.get("date_created", FIXED_DATETIME)
    mock_dataset.description = kwargs.get("description", "Test Description")
    mock_dataset.legend = kwargs.get("legend", {"col1": "Column 1"})
    mock_dataset.tags = kwargs.get("tags", ["tag1", "tag2"])

    mock_dataset.save = MagicMock()
    mock_dataset.delete = MagicMock()

    def setattr_mock(name, value):
        super(MagicMock, mock_dataset).__setattr__(name, value)

    mock_dataset.__setattr__ = setattr_mock
    return mock_dataset


def create_mock_datarow_db_object(**kwargs):
    mock_row = MagicMock(spec=DataRows)
    mock_row.id = kwargs.get("id", "row_123")
    mock_row.dataset_id = kwargs.get("dataset_id", 1)
    mock_row.data = kwargs.get("data", {"col1": 10, "col2": "a"})
    mock_row.location = kwargs.get("location", {"country": "US", "state": "CA"})
    mock_row.time = kwargs.get("time", {"year": 2023, "month": 1})

    mock_row.save = MagicMock()
    mock_row.delete = MagicMock()

    def setattr_mock(name, value):
        super(MagicMock, mock_row).__setattr__(name, value)

    mock_row.__setattr__ = setattr_mock
    return mock_row


class TestDatasetsRouter:
    def test_create_dataset_new_id(self, client, mocker):
        mocker.patch(
            "api.routes.datasets.datetime", now=MagicMock(return_value=FIXED_DATETIME)
        )

        mock_dataset_objects = mocker.patch("base.models.dataset.Dataset.objects")
        mock_dataset_objects.order_by.return_value.first.return_value = None

        mock_new_db_dataset = create_mock_dataset_db_object(
            dataset_id=1,
            title="New Dataset",
            author="user1",
            column_labels=["time", "value"],
            is_public=False,
            date_created=FIXED_DATETIME,
        )

        # Mock the Dataset class constructor to return our mock instance.
        # This mock_new_db_dataset will have dataset_id set by the endpoint logic.
        mock_dataset_class = mocker.patch(
            "base.models.dataset.Dataset", return_value=mock_new_db_dataset
        )

        dataset_payload = {
            "title": "New Dataset",
            "author": "user1",
            "column_labels": ["time", "value"],
            "is_public": False,
        }
        response = client.post("/datasets/", json=dataset_payload)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["dataset_id"] == 1  # Auto-generated
        assert json_response["title"] == "New Dataset"
        assert json_response["date_created"] == FIXED_DATETIME_STR

        # Ensure Dataset(**data) was called with correct dataset_id and date_created
        args, kwargs = mock_dataset_class.call_args
        assert kwargs["dataset_id"] == 1
        assert kwargs["date_created"] == FIXED_DATETIME
        mock_new_db_dataset.save.assert_called_once()

    def test_create_dataset_increment_id(self, client, mocker):
        mocker.patch(
            "api.routes.datasets.datetime", now=MagicMock(return_value=FIXED_DATETIME)
        )

        mock_latest_dataset = MagicMock(dataset_id=5)
        mock_dataset_objects = mocker.patch("base.models.dataset.Dataset.objects")
        mock_dataset_objects.order_by.return_value.first.return_value = (
            mock_latest_dataset
        )

        mock_new_db_dataset = create_mock_dataset_db_object(dataset_id=6)
        mock_dataset_class = mocker.patch(
            "base.models.dataset.Dataset", return_value=mock_new_db_dataset
        )

        dataset_payload = {
            "title": "Another Dataset",
            "author": "user2",
            "column_labels": ["a"],
            "is_public": True,
        }
        response = client.post("/datasets/", json=dataset_payload)

        assert response.status_code == 200
        assert response.json()["dataset_id"] == 6
        args, kwargs = mock_dataset_class.call_args
        assert kwargs["dataset_id"] == 6
        mock_new_db_dataset.save.assert_called_once()

    def test_get_dataset_success(self, client, mocker):
        mock_db_dataset = create_mock_dataset_db_object(
            dataset_id=1, title="Fetched Dataset"
        )
        mock_qs = MagicMock()
        mock_qs.first.return_value = mock_db_dataset
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.get("/datasets/1")
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["dataset_id"] == 1
        assert json_response["title"] == "Fetched Dataset"
        assert json_response["date_created"] == FIXED_DATETIME.isoformat()

    def test_get_dataset_not_found(self, client, mocker):
        mock_qs = MagicMock()
        mock_qs.first.return_value = None
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.get("/datasets/99")
        assert response.status_code == 404
        assert response.json()["detail"] == "Dataset not found"

    def test_update_dataset_success(self, client, mocker):
        mock_existing_dataset = create_mock_dataset_db_object(
            dataset_id=1, title="Old Title"
        )
        mock_qs = MagicMock()
        mock_qs.first.return_value = mock_existing_dataset
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        update_payload = {"title": "New Title", "is_public": False}
        response = client.put("/datasets/1", json=update_payload)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["title"] == "New Title"
        assert json_response["is_public"] is False

        assert mock_existing_dataset.title == "New Title"
        assert mock_existing_dataset.is_public is False
        mock_existing_dataset.save.assert_called_once()

    def test_update_dataset_not_found(self, client, mocker):
        mock_qs = MagicMock()
        mock_qs.first.return_value = None
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.put("/datasets/99", json={"title": "New Title"})
        assert response.status_code == 404

    def test_delete_dataset_success(self, client, mocker):
        mock_db_dataset = create_mock_dataset_db_object(dataset_id=1)
        mock_qs = MagicMock()
        mock_qs.first.return_value = mock_db_dataset
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.delete("/datasets/1")
        assert response.status_code == 200
        assert response.json() == {"message": "Dataset deleted"}
        mock_db_dataset.delete.assert_called_once()

    def test_delete_dataset_not_found(self, client, mocker):
        mock_qs = MagicMock()
        mock_qs.first.return_value = None
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.delete("/datasets/99")
        assert response.status_code == 404


class TestMetadataRouter:
    def test_update_metadata_success(self, client, mocker):
        mock_db_dataset = create_mock_dataset_db_object(
            dataset_id=1, legend={"old_col": "Old Name"}, tags=["old_tag"]
        )
        mock_qs = MagicMock()
        mock_qs.first.return_value = mock_db_dataset
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        update_payload = {
            "legend": {"new_col": "New Name"},
            "tags": ["new_tag1", "new_tag2"],
        }
        response = client.put("/datasets/1/metadata", json=update_payload)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["legend"] == {"new_col": "New Name"}
        assert json_response["tags"] == ["new_tag1", "new_tag2"]

        assert mock_db_dataset.legend == {"new_col": "New Name"}
        assert mock_db_dataset.tags == ["new_tag1", "new_tag2"]
        mock_db_dataset.save.assert_called_once()

    def test_update_metadata_partial(self, client, mocker):
        mock_db_dataset = create_mock_dataset_db_object(
            dataset_id=1, legend={"colA": "Name A"}, tags=["tagA"]
        )
        mock_qs = MagicMock()
        mock_qs.first.return_value = mock_db_dataset
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        update_payload = {"tags": ["tagB"]}
        response = client.put("/datasets/1/metadata", json=update_payload)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["legend"] == {"colA": "Name A"}
        assert json_response["tags"] == ["tagB"]
        mock_db_dataset.save.assert_called_once()

    def test_update_metadata_not_found(self, client, mocker):
        mock_qs = MagicMock()
        mock_qs.first.return_value = None
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.put("/datasets/99/metadata", json={"tags": ["new_tag"]})
        assert response.status_code == 404

    def test_get_metadata_success(self, client, mocker):
        mock_db_dataset = create_mock_dataset_db_object(
            dataset__id=1, legend={"col1": "Column One"}, tags=["weather", "temp"]
        )
        mock_qs = MagicMock()
        mock_qs.first.return_value = mock_db_dataset
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.get("/datasets/1/metadata")
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["legend"] == {"col1": "Column One"}
        assert json_response["tags"] == ["weather", "temp"]

    def test_get_metadata_not_found(self, client, mocker):
        mock_qs = MagicMock()
        mock_qs.first.return_value = None
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.get("/datasets/99/metadata")
        assert response.status_code == 404


class TestPropertiesRouter:
    def test_update_properties_success(self, client, mocker):
        mock_db_dataset = create_mock_dataset_db_object(
            dataset_id=1,
            is_public=True,
            column_labels=["old_col"],
            description="Old desc",
        )
        mock_qs = MagicMock()
        mock_qs.first.return_value = mock_db_dataset
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        update_payload = {
            "is_public": False,
            "column_labels": ["new_col1", "new_col2"],
            "description": "New desc",
        }
        response = client.put("/datasets/1/properties", json=update_payload)

        assert response.status_code == 200
        # Endpoint returns the update_data, not the full object
        assert response.json() == update_payload

        assert mock_db_dataset.is_public is False
        assert mock_db_dataset.column_labels == ["new_col1", "new_col2"]
        assert mock_db_dataset.description == "New desc"
        mock_db_dataset.save.assert_called_once()

    def test_update_properties_not_found(self, client, mocker):
        mock_qs = MagicMock()
        mock_qs.first.return_value = None
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.put("/datasets/99/properties", json={"is_public": True})
        assert response.status_code == 404

    def test_get_properties_success(self, client, mocker):
        mock_db_dataset = create_mock_dataset_db_object(
            dataset_id=1,
            is_public=False,
            column_labels=["temp", "humidity"],
            description="Weather data",
        )
        mock_qs = MagicMock()
        mock_qs.first.return_value = mock_db_dataset
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.get("/datasets/1/properties")
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["is_public"] is False
        assert json_response["column_labels"] == ["temp", "humidity"]
        assert json_response["description"] == "Weather data"

    def test_get_properties_not_found(self, client, mocker):
        mock_qs = MagicMock()
        mock_qs.first.return_value = None
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        response = client.get("/datasets/99/properties")
        assert response.status_code == 404


class TestRowsRouter:
    @pytest.fixture
    def mock_dataset_for_rows(self, mocker):
        mock_ds = create_mock_dataset_db_object(
            dataset_id=1, column_labels=["colA", "colB"]
        )
        mock_qs = MagicMock()
        mock_qs.first.return_value = mock_ds
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)
        return mock_ds

    def test_add_rows_success_validate_true(self, client, mocker):
        rows_payload = [
            {
                "data": {"colA": 1, "colB": "x"},
                "location": {"country": "US"},
                "time": {"year": 2023},
            },
            {
                "data": {"colA": 2, "colB": "y"},
                "location": {"country": "CA"},
                "time": {"year": 2024},
            },
        ]

        mock_row_instance_1 = create_mock_datarow_db_object(
            id="row1", dataset_id=1, data=rows_payload[0]["data"]
        )
        mock_row_instance_2 = create_mock_datarow_db_object(
            id="row2", dataset_id=1, data=rows_payload[1]["data"]
        )

        mock_datarows_class = mocker.patch(
            "base.models.dataset.DataRows",
            side_effect=[mock_row_instance_1, mock_row_instance_2],
        )

        response = client.post("/datasets/1/rows?validate=true", json=rows_payload)

        assert response.status_code == 200
        json_response = response.json()
        assert len(json_response) == 2
        assert json_response[0]["id"] == "row1"
        assert json_response[1]["id"] == "row2"
        assert json_response[0]["data"] == {"colA": 1, "colB": "x"}

        assert mock_datarows_class.call_count == 2
        mock_row_instance_1.save.assert_called_once()
        mock_row_instance_2.save.assert_called_once()

    def test_add_rows_invalid_column_names(self, client):
        rows_payload = [
            {"data": {"colC": 1}, "location": {"country": "US"}, "time": {"year": 2023}}
        ]
        response = client.post("/datasets/1/rows?validate=true", json=rows_payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid column names"

    def test_add_rows_dataset_not_found(self, client, mocker):
        mock_qs = MagicMock()
        mock_qs.first.return_value = None
        mocker.patch("base.models.dataset.Dataset.objects", return_value=mock_qs)

        rows_payload = [{"data": {}, "location": {}, "time": {}}]
        response = client.post("/datasets/99/rows", json=rows_payload)
        assert response.status_code == 404
        assert response.json()["detail"] == "Dataset not found"

    def test_get_rows_success(self, client, mocker):
        mock_row1 = create_mock_datarow_db_object(
            id="r1", dataset_id=1, data={"colA": 1}
        )
        mock_row2 = create_mock_datarow_db_object(
            id="r2", dataset_id=1, data={"colA": 2}
        )

        mock_datarows_qs = MagicMock()
        mock_datarows_qs.skip.return_value.limit.return_value = [mock_row1, mock_row2]

        mock_datarows_objects_manager = mocker.patch(
            "base.models.dataset.DataRows.objects"
        )
        mock_datarows_objects_manager.return_value = mock_datarows_qs

        response = client.get("/datasets/1/rows?skip=0&limit=10")
        assert response.status_code == 200
        json_response = response.json()
        assert len(json_response) == 2
        assert json_response[0]["id"] == "r1"
        assert json_response[1]["id"] == "r2"

        mock_datarows_objects_manager.assert_called_with(dataset_id=1)
        mock_datarows_qs.skip.assert_called_with(0)
        mock_datarows_qs.skip.return_value.limit.assert_called_with(10)

    def test_get_rows_with_filters(self, client, mocker):
        mock_row1 = create_mock_datarow_db_object(
            id="r1", dataset_id=1, data={"colA": 1}
        )

        mock_datarows_qs = MagicMock()
        mock_datarows_qs.skip.return_value.limit.return_value = [mock_row1]

        mock_datarows_objects_manager = mocker.patch(
            "base.models.dataset.DataRows.objects"
        )
        mock_datarows_objects_manager.return_value = mock_datarows_qs

        client.get("/datasets/1/rows?skip=0&limit=10&year=2023&country=US")
        mock_datarows_objects_manager.assert_called_with(
            dataset_id=1, year=2023, country="US"
        )

    def test_update_row_success(self, client, mocker):
        mock_existing_row = create_mock_datarow_db_object(
            id="rowxyz", dataset_id=1, data={"colA": 10}
        )

        mock_datarows_qs = MagicMock()
        mock_datarows_qs.first.return_value = mock_existing_row
        mock_datarows_objects_manager = mocker.patch(
            "base.models.dataset.DataRows.objects"
        )
        mock_datarows_objects_manager.return_value = mock_datarows_qs

        update_payload = {"data": {"colA": 20}, "location": {"country": "CA"}}
        response = client.put("/datasets/1/rows/rowxyz", json=update_payload)

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["data"]["colA"] == 20
        assert json_response["location"]["country"] == "CA"

        assert mock_existing_row.data == {"colA": 20}
        assert mock_existing_row.location == {"country": "CA"}
        mock_existing_row.save.assert_called_once()
        mock_datarows_objects_manager.assert_called_with(id="rowxyz", dataset_id=1)

    def test_update_row_not_found(self, client, mocker):
        mock_datarows_qs = MagicMock()
        mock_datarows_qs.first.return_value = None
        mock_datarows_objects_manager = mocker.patch(
            "base.models.dataset.DataRows.objects"
        )
        mock_datarows_objects_manager.return_value = mock_datarows_qs

        response = client.put(
            "/datasets/1/rows/nonexistent", json={"data": {"colA": 1}}
        )
        assert response.status_code == 404

    def test_delete_rows_with_ids(self, client, mocker):
        mock_datarows_qs = MagicMock()
        mock_datarows_qs.delete.return_value = 2

        mock_datarows_objects_manager = mocker.patch(
            "base.models.dataset.DataRows.objects"
        )
        mock_datarows_objects_manager.return_value = mock_datarows_qs

        response = client.delete("/datasets/1/rows?row_ids=id1&row_ids=id2")
        assert response.status_code == 200
        assert response.json() == {"deleted_count": 2}
        mock_datarows_objects_manager.assert_called_with(
            dataset_id=1, id__in=["id1", "id2"]
        )
        mock_datarows_qs.delete.assert_called_once()

    def test_delete_rows_all_for_dataset(self, client, mocker):
        mock_datarows_qs = MagicMock()
        mock_datarows_qs.delete.return_value = 5

        mock_datarows_objects_manager = mocker.patch(
            "base.models.dataset.DataRows.objects"
        )
        mock_datarows_objects_manager.return_value = mock_datarows_qs

        response = client.delete("/datasets/1/rows")
        assert response.status_code == 200
        assert response.json() == {"deleted_count": 5}
        mock_datarows_objects_manager.assert_called_with(dataset_id=1)
        mock_datarows_qs.delete.assert_called_once()
