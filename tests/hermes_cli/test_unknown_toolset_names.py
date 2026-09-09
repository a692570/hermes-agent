"""Unit tests for the ``unknown_toolset_names`` helper in hermes_cli.toolset_validation.

Pure logic - the validity predicate is injected, so these tests need neither the
tool registry nor a running Hermes. The helper backs the CLI constructor's
"Unknown toolsets" warning (see #78102): MCP server names and the ``no_mcp``
sentinel are legitimate entries that only resolve after MCP discovery, so the
constructor must not warn on them.
"""

from hermes_cli.toolset_validation import unknown_toolset_names

# Small representative set: the tests only need one valid toolset name.
_KNOWN = {"hermes-cli", "web", "terminal"}


def _is_valid(name):
    return name in _KNOWN


def test_prefixed_mcp_toolset_name_exempt():
    # The exact #78102 reproduction: 'mcp-codegraph' warned at startup for a configured
    # server. The prefixed form is the canonical MCP toolset name (tools/mcp_tool_registration.py
    # registers the mcp-<server> alias), so it must not warn.
    assert unknown_toolset_names(["mcp-codegraph"], _is_valid, {"codegraph"}) == []


def test_bare_mcp_server_name_exempt():
    # Today's bare-name exemption, now expressed through the helper.
    assert unknown_toolset_names(["codegraph"], _is_valid, {"codegraph"}) == []


def test_prefixed_unknown_suffix_still_flagged():
    # The exemption vouches for configured servers only: a prefixed name whose suffix
    # is not a configured server is genuinely unknown.
    assert unknown_toolset_names(["mcp-ghost"], _is_valid, {"codegraph"}) == ["mcp-ghost"]


def test_plain_garbage_still_flagged():
    assert unknown_toolset_names(["bogus"], _is_valid, {"codegraph"}) == ["bogus"]


def test_no_mcp_sentinel_exempt():
    # 'no_mcp' is the reserved "disable all MCP" sentinel (tools_config._merge_mcp_servers);
    # validate_toolset rejects it, so without the exemption it would false-warn.
    assert unknown_toolset_names(["no_mcp"], _is_valid, {"codegraph"}) == []


def test_order_preserved_with_multiple_unknowns():
    # Two unknowns among valid and exempt entries: both flagged, input order kept.
    assert unknown_toolset_names(
        ["bogus", "mcp-ghost", "web", "mcp-codegraph"], _is_valid, {"codegraph"}
    ) == ["bogus", "mcp-ghost"]


def test_non_str_entry_flagged_not_raised():
    # Pre-existing behavior: a non-str entry is flagged, not AttributeError'd.
    assert unknown_toolset_names([123], _is_valid, {"codegraph"}) == [123]


def test_no_configured_servers_flags_prefixed_but_not_sentinel():
    # mcp_server_names=None: no configured servers to vouch for the prefixed form, so it
    # warns again; the reserved sentinel stays exempt regardless of MCP config.
    assert unknown_toolset_names(["mcp-codegraph"], _is_valid, None) == ["mcp-codegraph"]
    assert unknown_toolset_names(["no_mcp"], _is_valid, None) == []
