from pathlib import Path

cwd = Path(__file__).parents[0]


def test_write_file_happy_path(api_client):
    filename = (
        cwd / 'files/firehol_webserver.netset'
    ).resolve()
    with open(filename, "rb") as f:
        response = api_client.put(
            "/lists/firehol_webserver",
            files={
                "file": (
                    "filename",
                    f,
                    "text",
                )
            }
        )
    assert response.status_code == 200
    assert response.json() == {
        'lines_processed': 2008
    }
    response = api_client.get(
        "/verify?lists=firehol_webserver&ip_address=2.49.190.6",
    )
    assert response.json() == {
        'is_bad': True,
        'reason': 'firehol_webserver',
    }

    response = api_client.get(
        "/verify?lists=firehol_webserver&ip_address=2.57.28.1",
    )
    assert response.json() == {
        'is_bad': True,
        'reason': 'firehol_webserver',
    }

    response = api_client.get(
        "/verify?lists=firehol_webserver&ip_address=1.1.1.1",
    )
    assert response.json() == {'is_bad': False}


def test_metadata(api_client):
    filename = (
        cwd / 'files/firehol_webserver.netset'
    ).resolve()
    with open(filename, "rb") as f:
        response = api_client.put(
            "/lists/firehol_webserver",
            files={
                "file": (
                    "filename",
                    f,
                    "text",
                )
            }
        )
    assert response.status_code == 200
    assert response.json() == {
        'lines_processed': 2008
    }
    response = api_client.get("/lists")
    final_data = response.json()
    assert final_data[0]['name'] == 'firehol_webserver'
    assert len(final_data) == 1

    filename = (
        cwd / 'files/firehol_level1.netset'
    ).resolve()
    with open(filename, "rb") as f:
        response = api_client.put(
            "/lists/firehol_level1",
            files={
                "file": (
                    "filename",
                    f,
                    "text",
                )
            }
        )
    assert response.status_code == 200
    response = api_client.get("/lists")
    final_data = response.json()
    assert len(final_data) == 2
    names = []
    for item in final_data:
        names.append(item['name'])

    assert 'firehol_webserver' in names
    assert 'firehol_level1' in names
    assert len(names) == 2
