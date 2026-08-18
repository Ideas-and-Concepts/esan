from unittest.mock import MagicMock, patch

import pytest

from modules.dashboard.services import get_production_summary


def test_get_production_summary_closes_session_when_milling_query_fails():
    """Database session must be closed if the MillingBatch query fails."""

    mock_db = MagicMock()

    # Make the MillingBatch query raise an exception.
    mock_db.query.side_effect = Exception(
        "MillingBatch database error"
    )

    with patch(
        "modules.dashboard.services.SessionLocal",
        return_value=mock_db,
    ):
        with pytest.raises(Exception, match="MillingBatch database error"):
            get_production_summary()

    # The session must always be closed.
    mock_db.close.assert_called_once()