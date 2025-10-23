"""Minimal Flask web front-end for gaiji conversion."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template_string, request

from gaiji_converter.converter import GaijiConverter, PlaceholderFallback
from gaiji_converter.datastore import GaijiDataStore

APP_TEMPLATE = """
<!doctype html>
<title>Gaiji Conversion</title>
<h1>Gaiji Conversion Workbench</h1>
<form method="post" action="{{ url_for('convert') }}">
  <label for="gaiji_ids">Gaiji IDs (space separated)</label>
  <input type="text" id="gaiji_ids" name="gaiji_ids" value="{{ gaiji_ids }}" size="60" />
  <button type="submit">Convert</button>
</form>
{% if results %}
  <h2>Results</h2>
  <table border="1" cellpadding="4">
    <tr><th>Gaiji ID</th><th>Replacement</th><th>Strategy</th><th>Notes</th></tr>
    {% for result in results %}
      <tr>
        <td>{{ result.gaiji_id }}</td>
        <td>{{ result.replacement }}</td>
        <td>{{ result.strategy }}</td>
        <td>{{ result.notes or '' }}</td>
      </tr>
    {% endfor %}
  </table>
  <p><strong>Output:</strong> {{ output }}</p>
{% endif %}
<h2>Dictionary Snapshot</h2>
<table border="1" cellpadding="4">
  <tr><th>Gaiji ID</th><th>Character</th><th>Unicode</th><th>Reading</th><th>Notes</th></tr>
  {% for entry in entries %}
    <tr>
      <td>{{ entry.gaiji_id }}</td>
      <td>{{ entry.character }}</td>
      <td>{{ entry.unicode_codepoint }}</td>
      <td>{{ entry.reading }}</td>
      <td>{{ entry.notes }}</td>
    </tr>
  {% endfor %}
</table>
"""


def create_app(database: Path | None = None) -> Flask:
    app = Flask(__name__)
    db_path = database or Path("gaiji_web.sqlite3")
    datastore = GaijiDataStore(db_path)
    datastore.initialize(Path("db/schema.sql"))
    datastore.load_csv(Path("data/gaiji_mappings.csv"))
    converter = GaijiConverter(datastore, [PlaceholderFallback()])

    @app.route("/", methods=["GET"])
    def index():
        entries = list(datastore.iter_entries())
        return render_template_string(
            APP_TEMPLATE,
            entries=entries,
            results=None,
            output="",
            gaiji_ids="",
        )

    @app.route("/convert", methods=["POST"])
    def convert():
        gaiji_ids = request.form.get("gaiji_ids", "").split()
        results = converter.convert_tokens(gaiji_ids) if gaiji_ids else []
        output = "".join(result.replacement for result in results)
        entries = list(datastore.iter_entries())
        return render_template_string(
            APP_TEMPLATE,
            entries=entries,
            results=results,
            output=output,
            gaiji_ids=" ".join(gaiji_ids),
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
