import json
import csv
import os


def test_export_json(client, hunt, tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda _: str(tmp_path))
    r = client.get("/api/export?scope=all&format=json")
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert data["filename"] == "shiny-trak-all.json"
    filepath = tmp_path / "Downloads" / "shiny-trak-all.json"
    assert filepath.exists()
    exported = json.loads(filepath.read_text())
    assert any(h["id"] == hunt["id"] for h in exported)


def test_export_csv(client, hunt, tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda _: str(tmp_path))
    r = client.get("/api/export?scope=all&format=csv")
    assert r.status_code == 200
    assert r.get_json()["filename"] == "shiny-trak-all.csv"
    filepath = tmp_path / "Downloads" / "shiny-trak-all.csv"
    assert filepath.exists()
    rows = list(csv.DictReader(filepath.read_text().splitlines()))
    assert any(row["displayName"] == "Pikachu" for row in rows)


def test_export_active_only(client, hunt, tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda _: str(tmp_path))
    client.post(f"/api/hunts/{hunt['id']}/complete", json={})
    r = client.get("/api/export?scope=active&format=json")
    assert r.status_code == 200
    filepath = tmp_path / "Downloads" / "shiny-trak-active.json"
    exported = json.loads(filepath.read_text())
    assert all(h.get("status", "active") == "active" for h in exported)


def test_export_completed_only(client, hunt, tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda _: str(tmp_path))
    client.post(f"/api/hunts/{hunt['id']}/complete", json={})
    r = client.get("/api/export?scope=completed&format=json")
    assert r.status_code == 200
    filepath = tmp_path / "Downloads" / "shiny-trak-completed.json"
    exported = json.loads(filepath.read_text())
    assert all(h["status"] == "completed" for h in exported)
    assert any(h["id"] == hunt["id"] for h in exported)
