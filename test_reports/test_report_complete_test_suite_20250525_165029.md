# Test Results Report

**Generated**: 2025-05-25 16:50:29  
**Suite**: complete_test_suite  
**Total Duration**: 91.25s  

---


## Test Suite Summary

| Metric | Value |
|--------|-------|
| **Test Suite** | complete_test_suite |
| **Start Time** | 2025-05-25 16:48:57 |
| **Duration** | 91.25s |
| **Total Tests** | 106 |
| **✅ Passed** | 0 |
| **❌ Failed** | 0 |
| **⚠️ Errors** | 106 |
| **⏭️ Skipped** | 0 |
| **Success Rate** | 0.0% |
| **Status** | ❌ FAILURES DETECTED |



## Detailed Test Results

| Test ID | Module | Status | Duration | Description | ArangoDB Results | Assertion Details |
|---------|--------|--------|----------|-------------|------------------|-------------------|
| `test_all_cli_commands.py::TestAllCLICommands::test_main_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_memory_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_search_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_graph_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_crud_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_episode_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_compaction_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_search_config_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_all_cli_commands.py:85: in test_search_config_help
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Re... |
| `test_all_cli_commands.py::TestAllCLICommands::test_validate_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_all_cli_commands.py:92: in test_validate_help
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result ... |
| `test_all_cli_commands.py::TestAllCLICommands::test_community_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_contradiction_help` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_json_output_consistency` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_table_output_consistency` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_parameter_consistency` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_all_cli_commands.py::TestAllCLICommands::test_error_handling_consistency` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_detect_default` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:140: in test_community_detect_default
    assert result.exit_code == 0
E   assert 2 == 0
E    +  wher... |
| `test_community_commands.py::TestCommunityCommands::test_community_detect_with_algorithm` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:158: in test_community_detect_with_algorithm
    assert result.exit_code == 0
E   assert 2 == 0
E    ... |
| `test_community_commands.py::TestCommunityCommands::test_community_list` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:181: in test_community_list
    assert data["success"] is True
E   KeyError: 'success' |
| `test_community_commands.py::TestCommunityCommands::test_community_show` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:199: in test_community_show
    detect_data = json.loads(detect_result.stdout)
../../../.local/share/... |
| `test_community_commands.py::TestCommunityCommands::test_community_members` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:224: in test_community_members
    detect_data = json.loads(detect_result.stdout)
../../../.local/sha... |
| `test_community_commands.py::TestCommunityCommands::test_community_detect_with_resolution` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:262: in test_community_detect_with_resolution
    assert result_low.exit_code == 0
E   assert 2 == 0
... |
| `test_community_commands.py::TestCommunityCommands::test_community_detect_with_min_size` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:281: in test_community_detect_with_min_size
    assert result.exit_code == 0
E   assert 2 == 0
E    +... |
| `test_community_commands.py::TestCommunityCommands::test_community_stats` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:304: in test_community_stats
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Re... |
| `test_community_commands.py::TestCommunityCommands::test_community_merge` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:320: in test_community_merge
    detect_data = json.loads(detect_result.stdout)
../../../.local/share... |
| `test_community_commands.py::TestCommunityCommands::test_community_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:345: in test_community_table_output
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where ... |
| `test_community_commands.py::TestCommunityCommands::test_community_export` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:365: in test_community_export
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <R... |
| `test_community_commands.py::TestCommunityCommands::test_community_invalid_algorithm` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_community_commands.py::TestCommunityCommands::test_community_empty_collection` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_community_commands.py:396: in test_community_empty_collection
    assert result.exit_code == 0
E   assert 2 == 0
E    +  wh... |
| `test_crud_commands.py::TestCrudCommands::test_crud_create_basic` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_create_with_embedding` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_read_by_key` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_read_not_found` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:114: in test_crud_read_not_found
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Res... |
| `test_crud_commands.py::TestCrudCommands::test_crud_update_document` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:130: in test_crud_update_document
    assert data["data"]["price"] == 59.99
E   assert 49.99 == 59.99 |
| `test_crud_commands.py::TestCrudCommands::test_crud_update_with_embedding` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:158: in test_crud_update_with_embedding
    assert data["data"]["content"] == "Completely different conten... |
| `test_crud_commands.py::TestCrudCommands::test_crud_delete_document` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:180: in test_crud_delete_document
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Re... |
| `test_crud_commands.py::TestCrudCommands::test_crud_list_default` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:203: in test_crud_list_default
    assert len(data["data"]["documents"]) >= 2
E   TypeError: list indices ... |
| `test_crud_commands.py::TestCrudCommands::test_crud_list_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:221: in test_crud_list_with_limit
    assert len(data["data"]["documents"]) == 1
E   TypeError: list indic... |
| `test_crud_commands.py::TestCrudCommands::test_crud_list_with_filter` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:231: in test_crud_list_with_filter
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <R... |
| `test_crud_commands.py::TestCrudCommands::test_crud_list_empty_collection` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:254: in test_crud_list_empty_collection
    assert data["data"]["documents"] == []
E   TypeError: list ind... |
| `test_crud_commands.py::TestCrudCommands::test_crud_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:265: in test_crud_table_output
    assert "_key" in result.stdout
E   assert '_key' in '                  ... |
| `test_crud_commands.py::TestCrudCommands::test_crud_create_invalid_json` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_crud_commands.py::TestCrudCommands::test_crud_cross_collection` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:300: in test_crud_cross_collection
    assert len(list_data["data"]["documents"]) >= 2
E   TypeError: list... |
| `test_crud_commands.py::TestCrudCommands::test_crud_update_nonexistent` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:310: in test_crud_update_nonexistent
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = ... |
| `test_crud_commands.py::TestCrudCommands::test_crud_create_with_special_chars` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_crud_commands.py:323: in test_crud_create_with_special_chars
    assert result.exit_code == 0
E   assert 1 == 0
E    +  whe... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_create_basic` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:124: in test_episode_create_basic
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = ... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_create_with_metadata` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:142: in test_episode_create_with_metadata
    assert result.exit_code == 0
E   assert 2 == 0
E    +  wh... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_list_all` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:156: in test_episode_list_all
    data = json.loads(result.stdout)
../../../.local/share/uv/python/cpyt... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_list_active_only` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:176: in test_episode_list_active_only
    data = json.loads(result.stdout)
../../../.local/share/uv/pyt... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_list_by_type` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:192: in test_episode_list_by_type
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = ... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_get_by_id` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:208: in test_episode_get_by_id
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Re... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_get_conversations` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:222: in test_episode_get_conversations
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_update_title` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:240: in test_episode_update_title
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = ... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_close` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:256: in test_episode_close
    create_data = json.loads(create_result.stdout)
../../../.local/share/uv/... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_close_already_closed` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:280: in test_episode_close_already_closed
    assert result.exit_code == 0
E   assert 2 == 0
E    +  wh... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_current` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:292: in test_episode_current
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Resu... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:311: in test_episode_table_output
    assert "Title" in result.stdout
E   AssertionError: assert 'Title... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_invalid_id` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:323: in test_episode_invalid_id
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <R... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_list_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_episode_commands.py:338: in test_episode_list_with_limit
    assert data["success"] is True
E   TypeError: list indices mus... |
| `test_episode_commands.py::TestEpisodeCommands::test_episode_create_invalid_metadata` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_graph_commands.py::TestGraphCommands::test_graph_add_relationship` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:126: in test_graph_add_relationship
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = ... |
| `test_graph_commands.py::TestGraphCommands::test_graph_add_duplicate_relationship` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:153: in test_graph_add_duplicate_relationship
    assert result2.exit_code == 0
E   assert 1 == 0
E    + ... |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_outbound` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:168: in test_graph_traverse_outbound
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 =... |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_inbound` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:186: in test_graph_traverse_inbound
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = ... |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_any_direction` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:204: in test_graph_traverse_any_direction
    assert result.exit_code == 0
E   assert 2 == 0
E    +  wher... |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_with_filter` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:222: in test_graph_traverse_with_filter
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where ... |
| `test_graph_commands.py::TestGraphCommands::test_graph_visualize` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:240: in test_graph_visualize
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result... |
| `test_graph_commands.py::TestGraphCommands::test_graph_delete_relationship` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:264: in test_graph_delete_relationship
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2... |
| `test_graph_commands.py::TestGraphCommands::test_graph_traverse_nonexistent_node` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:291: in test_graph_traverse_nonexistent_node
    assert result.exit_code == 0
E   assert 2 == 0
E    +  w... |
| `test_graph_commands.py::TestGraphCommands::test_graph_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:304: in test_graph_table_output
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Res... |
| `test_graph_commands.py::TestGraphCommands::test_graph_add_relationship_invalid_type` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_graph_commands.py::TestGraphCommands::test_graph_stats` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:328: in test_graph_stats
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result Sys... |
| `test_graph_commands.py::TestGraphCommands::test_graph_subgraph` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_graph_commands.py:345: in test_graph_subgraph
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result ... |
| `test_memory_commands.py::TestMemoryCommands::test_memory_create_basic` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_create_with_metadata` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_list_default` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_list_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_list_by_conversation` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_search_basic` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_search_with_threshold` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_get_by_id` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_get_invalid_id` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_history_recent` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_history_by_conversation` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_history_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_create_with_entities` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_memory_commands.py::TestMemoryCommands::test_memory_search_empty_results` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_bm25_search_default` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:110: in test_bm25_search_default
    assert len(data["data"]["results"]) > 0
E   assert 0 > 0
E    +  wh... |
| `test_search_commands.py::TestSearchCommands::test_bm25_search_custom_collection` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:137: in test_bm25_search_custom_collection
    assert "Python programming" in first_result["doc"]["conte... |
| `test_search_commands.py::TestSearchCommands::test_semantic_search_default` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_semantic_search_with_threshold` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_semantic_search_with_tags` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_keyword_search` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:211: in test_keyword_search
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result... |
| `test_search_commands.py::TestSearchCommands::test_tag_search_single_tag` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_tag_search_multiple_tags_any` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:246: in test_tag_search_multiple_tags_any
    assert result.exit_code == 0
E   assert 2 == 0
E    +  whe... |
| `test_search_commands.py::TestSearchCommands::test_tag_search_multiple_tags_all` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:264: in test_tag_search_multiple_tags_all
    assert result.exit_code == 0
E   assert 2 == 0
E    +  whe... |
| `test_search_commands.py::TestSearchCommands::test_graph_search` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:308: in test_graph_search
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result S... |
| `test_search_commands.py::TestSearchCommands::test_search_with_limit` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_search_table_output` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:346: in test_search_table_output
    assert "Content" in result.stdout
E   assert 'Content' in "        ... |
| `test_search_commands.py::TestSearchCommands::test_search_error_handling` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries |  |
| `test_search_commands.py::TestSearchCommands::test_search_empty_query` | cli | ⚠️ ERROR | 0.000s | Test from cli | No DB queries | tests/arangodb/cli/test_search_commands.py:370: in test_search_empty_query
    assert result.exit_code != 0
E   assert 0 != 0
E    +  where 0 = <Re... |
| `tests/unit/test_community_detection_unit.py::test_init` | unit | ⚠️ ERROR | 0.000s | Test from unit | No DB queries |  |
| `tests/unit/test_community_detection_unit.py::test_adjacency_matrix` | unit | ⚠️ ERROR | 0.000s | Test from unit | No DB queries |  |
| `tests/unit/test_community_detection_unit.py::test_modularity` | unit | ⚠️ ERROR | 0.000s | Test from unit | No DB queries |  |
| `tests/unit/test_community_detection_unit.py::test_small_community_merging` | unit | ⚠️ ERROR | 0.000s | Test from unit | No DB queries |  |
| `tests/unit/test_community_detection_unit.py::test_empty_graph` | unit | ⚠️ ERROR | 0.000s | Test from unit | No DB queries |  |



## 🗄️ ArangoDB Summary

No database queries executed in this test suite.



## ❌ Failure Details (106 failures)

### test_all_cli_commands.py::TestAllCLICommands::test_main_help - test_main_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_memory_help - test_memory_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_search_help - test_search_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_graph_help - test_graph_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_crud_help - test_crud_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_episode_help - test_episode_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_compaction_help - test_compaction_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_search_config_help - test_search_config_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_all_cli_commands.py:85: in test_search_config_help
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_all_cli_commands.py::TestAllCLICommands::test_validate_help - test_validate_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_all_cli_commands.py:92: in test_validate_help
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_all_cli_commands.py::TestAllCLICommands::test_community_help - test_community_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_contradiction_help - test_contradiction_help

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_json_output_consistency - test_json_output_consistency

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_table_output_consistency - test_table_output_consistency

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_parameter_consistency - test_parameter_consistency

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_all_cli_commands.py::TestAllCLICommands::test_error_handling_consistency - test_error_handling_consistency

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_detect_default - test_community_detect_default

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:140: in test_community_detect_default
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_community_commands.py::TestCommunityCommands::test_community_detect_with_algorithm - test_community_detect_with_algorithm

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:158: in test_community_detect_with_algorithm
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_community_commands.py::TestCommunityCommands::test_community_list - test_community_list

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:181: in test_community_list
    assert data["success"] is True
E   KeyError: 'success'
```

---

### test_community_commands.py::TestCommunityCommands::test_community_show - test_community_show

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:199: in test_community_show
    detect_data = json.loads(detect_result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_community_commands.py::TestCommunityCommands::test_community_members - test_community_members

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:224: in test_community_members
    detect_data = json.loads(detect_result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_community_commands.py::TestCommunityCommands::test_community_detect_with_resolution - test_community_detect_with_resolution

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:262: in test_community_detect_with_resolution
    assert result_low.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_community_commands.py::TestCommunityCommands::test_community_detect_with_min_size - test_community_detect_with_min_size

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:281: in test_community_detect_with_min_size
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_community_commands.py::TestCommunityCommands::test_community_stats - test_community_stats

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:304: in test_community_stats
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_community_commands.py::TestCommunityCommands::test_community_merge - test_community_merge

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:320: in test_community_merge
    detect_data = json.loads(detect_result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_community_commands.py::TestCommunityCommands::test_community_table_output - test_community_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:345: in test_community_table_output
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_community_commands.py::TestCommunityCommands::test_community_export - test_community_export

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:365: in test_community_export
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_community_commands.py::TestCommunityCommands::test_community_invalid_algorithm - test_community_invalid_algorithm

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_community_commands.py::TestCommunityCommands::test_community_empty_collection - test_community_empty_collection

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_community_commands.py:396: in test_community_empty_collection
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_create_basic - test_crud_create_basic

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_create_with_embedding - test_crud_create_with_embedding

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_read_by_key - test_crud_read_by_key

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_read_not_found - test_crud_read_not_found

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:114: in test_crud_read_not_found
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_update_document - test_crud_update_document

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:130: in test_crud_update_document
    assert data["data"]["price"] == 59.99
E   assert 49.99 == 59.99
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_update_with_embedding - test_crud_update_with_embedding

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:158: in test_crud_update_with_embedding
    assert data["data"]["content"] == "Completely different content about quantum computing"
E   AssertionError: assert 'Original content' == 'Completely different content about quantum computing'
E     
E     - Completely different content about quantum computing
E     + Original content
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_delete_document - test_crud_delete_document

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:180: in test_crud_delete_document
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_list_default - test_crud_list_default

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:203: in test_crud_list_default
    assert len(data["data"]["documents"]) >= 2
E   TypeError: list indices must be integers or slices, not str
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_list_with_limit - test_crud_list_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:221: in test_crud_list_with_limit
    assert len(data["data"]["documents"]) == 1
E   TypeError: list indices must be integers or slices, not str
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_list_with_filter - test_crud_list_with_filter

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:231: in test_crud_list_with_filter
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_list_empty_collection - test_crud_list_empty_collection

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:254: in test_crud_list_empty_collection
    assert data["data"]["documents"] == []
E   TypeError: list indices must be integers or slices, not str
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_table_output - test_crud_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:265: in test_crud_table_output
    assert "_key" in result.stdout
E   assert '_key' in '                           Documents in test_products                           \n\u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n\u2503  Key      \u2503 Name         \u2503 Price \u2503 Category    \u2503 Tags                        \u2503\n\u2521\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2529\n\u2502 prod_001  \u2502 Widget Pro   \u2502 29.99 \u2502 tools       \u2502 ["professional",            \u2502\n\u2502           \u2502              \u2502       \u2502             \u2502 "durable"]...               \u2502\n\u2502 prod_002  \u2502 Gadget Plus  \u2502 49.99 \u2502 electronics \u2502 ["smart", "wireless"]...    \u2502\n\u2502 479284877 \u2502 Test Product \u2502 19.99 \u2502             \u2502                             \u2502\n\u2502 479285013 \u2502 Temp Product \u2502 9.99  \u2502             \u2502                             \u2502\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n                            Showing 4 of 4 documents                            \n'
E    +  where '                           Documents in test_products                           \n\u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n\u2503  Key      \u2503 Name         \u2503 Price \u2503 Category    \u2503 Tags                        \u2503\n\u2521\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2529\n\u2502 prod_001  \u2502 Widget Pro   \u2502 29.99 \u2502 tools       \u2502 ["professional",            \u2502\n\u2502           \u2502              \u2502       \u2502             \u2502 "durable"]...               \u2502\n\u2502 prod_002  \u2502 Gadget Plus  \u2502 49.99 \u2502 electronics \u2502 ["smart", "wireless"]...    \u2502\n\u2502 479284877 \u2502 Test Product \u2502 19.99 \u2502             \u2502                             \u2502\n\u2502 479285013 \u2502 Temp Product \u2502 9.99  \u2502             \u2502                             \u2502\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n                            Showing 4 of 4 documents                            \n' = <Result okay>.stdout
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_create_invalid_json - test_crud_create_invalid_json

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_crud_commands.py::TestCrudCommands::test_crud_cross_collection - test_crud_cross_collection

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:300: in test_crud_cross_collection
    assert len(list_data["data"]["documents"]) >= 2
E   TypeError: list indices must be integers or slices, not str
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_update_nonexistent - test_crud_update_nonexistent

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:310: in test_crud_update_nonexistent
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_crud_commands.py::TestCrudCommands::test_crud_create_with_special_chars - test_crud_create_with_special_chars

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_crud_commands.py:323: in test_crud_create_with_special_chars
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_create_basic - test_episode_create_basic

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:124: in test_episode_create_basic
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_create_with_metadata - test_episode_create_with_metadata

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:142: in test_episode_create_with_metadata
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_list_all - test_episode_list_all

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:156: in test_episode_list_all
    data = json.loads(result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:353: in raw_decode
    obj, end = self.scan_once(s, idx)
E   json.decoder.JSONDecodeError: Invalid control character at: line 49 column 46 (char 1555)
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_list_active_only - test_episode_list_active_only

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:176: in test_episode_list_active_only
    data = json.loads(result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:353: in raw_decode
    obj, end = self.scan_once(s, idx)
E   json.decoder.JSONDecodeError: Invalid control character at: line 49 column 46 (char 1555)
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_list_by_type - test_episode_list_by_type

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:192: in test_episode_list_by_type
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_get_by_id - test_episode_get_by_id

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:208: in test_episode_get_by_id
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_get_conversations - test_episode_get_conversations

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:222: in test_episode_get_conversations
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_update_title - test_episode_update_title

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:240: in test_episode_update_title
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_close - test_episode_close

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:256: in test_episode_close
    create_data = json.loads(create_result.stdout)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/__init__.py:346: in loads
    return _default_decoder.decode(s)
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:337: in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
../../../.local/share/uv/python/cpython-3.10.11-linux-x86_64-gnu/lib/python3.10/json/decoder.py:355: in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
E   json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_close_already_closed - test_episode_close_already_closed

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:280: in test_episode_close_already_closed
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_current - test_episode_current

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:292: in test_episode_current
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_table_output - test_episode_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:311: in test_episode_table_output
    assert "Title" in result.stdout
E   AssertionError: assert 'Title' in '                                  All Episodes                                  \n\u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n\u2503 Key           \u2503 Name         \u2503 Status \u2503 Start Time    \u2503 Entities \u2503 Relations \u2503\n\u2521\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2529\n\u2502 episode_5a9d\u2026 \u2502 CLI Test     \u2502 Active \u2502 2025-05-24T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502               \u2502 Episode      \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502 episode_cb78\u2026 \u2502 test_episod\u2026 \u2502 Active \u2502 2025-05-24T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502 episode_88b5\u2026 \u2502 Test Episode \u2502 Active \u2502 2025-05-17T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502 episode_7859\u2026 \u2502 Conversation \u2502 Active \u2502 2025-05-17T1\u2026 \u2502 4        \u2502 1         \u2502\n\u2502               \u2502 ccad6e59     \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502 episode_dd8f\u2026 \u2502 Conversation \u2502 Active \u2502 2025-05-17T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502               \u2502 b6d1d0b8     \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502 episode_5447\u2026 \u2502 Product      \u2502 Active \u2502 2025-05-17T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502               \u2502 Discussion   \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502               \u2502 Episode      \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502 episode_c190\u2026 \u2502 Python       \u2502 Active \u2502 2025-05-17T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502               \u2502 Framework    \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502               \u2502 Discussion   \u2502        \u2502               \u2502          \u2502           \u2502\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 \u2139\ufe0f INFO \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n\u2502 Showing 7 episodes                                                           \u2502\n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n'
E    +  where '                                  All Episodes                                  \n\u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n\u2503 Key           \u2503 Name         \u2503 Status \u2503 Start Time    \u2503 Entities \u2503 Relations \u2503\n\u2521\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2529\n\u2502 episode_5a9d\u2026 \u2502 CLI Test     \u2502 Active \u2502 2025-05-24T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502               \u2502 Episode      \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502 episode_cb78\u2026 \u2502 test_episod\u2026 \u2502 Active \u2502 2025-05-24T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502 episode_88b5\u2026 \u2502 Test Episode \u2502 Active \u2502 2025-05-17T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502 episode_7859\u2026 \u2502 Conversation \u2502 Active \u2502 2025-05-17T1\u2026 \u2502 4        \u2502 1         \u2502\n\u2502               \u2502 ccad6e59     \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502 episode_dd8f\u2026 \u2502 Conversation \u2502 Active \u2502 2025-05-17T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502               \u2502 b6d1d0b8     \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502 episode_5447\u2026 \u2502 Product      \u2502 Active \u2502 2025-05-17T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502               \u2502 Discussion   \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502               \u2502 Episode      \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502 episode_c190\u2026 \u2502 Python       \u2502 Active \u2502 2025-05-17T1\u2026 \u2502 0        \u2502 0         \u2502\n\u2502               \u2502 Framework    \u2502        \u2502               \u2502          \u2502           \u2502\n\u2502               \u2502 Discussion   \u2502        \u2502               \u2502          \u2502           \u2502\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n\u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 \u2139\ufe0f INFO \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n\u2502 Showing 7 episodes                                                           \u2502\n\u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n' = <Result okay>.stdout
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_invalid_id - test_episode_invalid_id

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:323: in test_episode_invalid_id
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_list_with_limit - test_episode_list_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_episode_commands.py:338: in test_episode_list_with_limit
    assert data["success"] is True
E   TypeError: list indices must be integers or slices, not str
```

---

### test_episode_commands.py::TestEpisodeCommands::test_episode_create_invalid_metadata - test_episode_create_invalid_metadata

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_graph_commands.py::TestGraphCommands::test_graph_add_relationship - test_graph_add_relationship

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:126: in test_graph_add_relationship
    assert result.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_add_duplicate_relationship - test_graph_add_duplicate_relationship

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:153: in test_graph_add_duplicate_relationship
    assert result2.exit_code == 0
E   assert 1 == 0
E    +  where 1 = <Result SystemExit(1)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_outbound - test_graph_traverse_outbound

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:168: in test_graph_traverse_outbound
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_inbound - test_graph_traverse_inbound

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:186: in test_graph_traverse_inbound
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_any_direction - test_graph_traverse_any_direction

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:204: in test_graph_traverse_any_direction
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_with_filter - test_graph_traverse_with_filter

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:222: in test_graph_traverse_with_filter
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_visualize - test_graph_visualize

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:240: in test_graph_visualize
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_delete_relationship - test_graph_delete_relationship

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:264: in test_graph_delete_relationship
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_traverse_nonexistent_node - test_graph_traverse_nonexistent_node

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:291: in test_graph_traverse_nonexistent_node
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_table_output - test_graph_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:304: in test_graph_table_output
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_add_relationship_invalid_type - test_graph_add_relationship_invalid_type

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_graph_commands.py::TestGraphCommands::test_graph_stats - test_graph_stats

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:328: in test_graph_stats
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_graph_commands.py::TestGraphCommands::test_graph_subgraph - test_graph_subgraph

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_graph_commands.py:345: in test_graph_subgraph
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_memory_commands.py::TestMemoryCommands::test_memory_create_basic - test_memory_create_basic

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_create_with_metadata - test_memory_create_with_metadata

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_list_default - test_memory_list_default

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_list_with_limit - test_memory_list_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_list_by_conversation - test_memory_list_by_conversation

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_search_basic - test_memory_search_basic

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_search_with_threshold - test_memory_search_with_threshold

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_get_by_id - test_memory_get_by_id

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_get_invalid_id - test_memory_get_invalid_id

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_history_recent - test_memory_history_recent

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_history_by_conversation - test_memory_history_by_conversation

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_history_with_limit - test_memory_history_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_table_output - test_memory_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_create_with_entities - test_memory_create_with_entities

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_memory_commands.py::TestMemoryCommands::test_memory_search_empty_results - test_memory_search_empty_results

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_bm25_search_default - test_bm25_search_default

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:110: in test_bm25_search_default
    assert len(data["data"]["results"]) > 0
E   assert 0 > 0
E    +  where 0 = len([])
```

---

### test_search_commands.py::TestSearchCommands::test_bm25_search_custom_collection - test_bm25_search_custom_collection

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:137: in test_bm25_search_custom_collection
    assert "Python programming" in first_result["doc"]["content"]
E   AssertionError: assert 'Python programming' in 'Python is a high-level programming language known for its simplicity and readability'
```

---

### test_search_commands.py::TestSearchCommands::test_semantic_search_default - test_semantic_search_default

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_semantic_search_with_threshold - test_semantic_search_with_threshold

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_semantic_search_with_tags - test_semantic_search_with_tags

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_keyword_search - test_keyword_search

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:211: in test_keyword_search
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_search_commands.py::TestSearchCommands::test_tag_search_single_tag - test_tag_search_single_tag

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_tag_search_multiple_tags_any - test_tag_search_multiple_tags_any

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:246: in test_tag_search_multiple_tags_any
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_search_commands.py::TestSearchCommands::test_tag_search_multiple_tags_all - test_tag_search_multiple_tags_all

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:264: in test_tag_search_multiple_tags_all
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_search_commands.py::TestSearchCommands::test_graph_search - test_graph_search

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:308: in test_graph_search
    assert result.exit_code == 0
E   assert 2 == 0
E    +  where 2 = <Result SystemExit(2)>.exit_code
```

---

### test_search_commands.py::TestSearchCommands::test_search_with_limit - test_search_with_limit

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_search_table_output - test_search_table_output

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:346: in test_search_table_output
    assert "Content" in result.stdout
E   assert 'Content' in "                                Semantic Results                                \n\u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n\u2503 Doc                                \u2503 Similarity Score   \u2503 Score              \u2503\n\u2521\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2529\n\u2502 {'_id': 'documents/test_doc_2',    \u2502 0.7861812114715576 \u2502 0.7861812114715576 \u2502\n\u2502 '_key': 'test_doc_...              \u2502                    \u2502                    \u2502\n\u2502 {'_id': 'documents/db_doc_1',      \u2502 0.7752950191497803 \u2502 0.7752950191497803 \u2502\n\u2502 '_key': 'db_doc_1', ...            \u2502                    \u2502                    \u2502\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n                                Found 2 results                                 \n"
E    +  where "                                Semantic Results                                \n\u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2533\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n\u2503 Doc                                \u2503 Similarity Score   \u2503 Score              \u2503\n\u2521\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2547\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2529\n\u2502 {'_id': 'documents/test_doc_2',    \u2502 0.7861812114715576 \u2502 0.7861812114715576 \u2502\n\u2502 '_key': 'test_doc_...              \u2502                    \u2502                    \u2502\n\u2502 {'_id': 'documents/db_doc_1',      \u2502 0.7752950191497803 \u2502 0.7752950191497803 \u2502\n\u2502 '_key': 'db_doc_1', ...            \u2502                    \u2502                    \u2502\n\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n                                Found 2 results                                 \n" = <Result okay>.stdout
```

---

### test_search_commands.py::TestSearchCommands::test_search_error_handling - test_search_error_handling

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

---

### test_search_commands.py::TestSearchCommands::test_search_empty_query - test_search_empty_query

**Module**: cli  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from cli  

**Error Message**:
```
tests/arangodb/cli/test_search_commands.py:370: in test_search_empty_query
    assert result.exit_code != 0
E   assert 0 != 0
E    +  where 0 = <Result okay>.exit_code
```

---

### tests/unit/test_community_detection_unit.py::test_init - test_init

**Module**: unit  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from unit  

---

### tests/unit/test_community_detection_unit.py::test_adjacency_matrix - test_adjacency_matrix

**Module**: unit  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from unit  

---

### tests/unit/test_community_detection_unit.py::test_modularity - test_modularity

**Module**: unit  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from unit  

---

### tests/unit/test_community_detection_unit.py::test_small_community_merging - test_small_community_merging

**Module**: unit  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from unit  

---

### tests/unit/test_community_detection_unit.py::test_empty_graph - test_empty_graph

**Module**: unit  
**Status**: ERROR  
**Duration**: 0.000s  

**Description**: Test from unit  

---



## 📊 Test Execution Timeline

| Test | Start Time | Duration | Status |
|------|------------|----------|--------|
| test_main_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_search_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_compaction_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_search_config_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_validate_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_contradiction_help | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_json_output_consistency | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_table_output_consistency | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_parameter_consistency | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_error_handling_consistency | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_detect_default | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_detect_with_algorithm | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_list | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_show | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_members | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_detect_with_resolution | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_detect_with_min_size | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_stats | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_merge | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_table_output | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_export | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_invalid_algorithm | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_community_empty_collection | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_create_basic | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_create_with_embedding | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_read_by_key | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_read_not_found | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_update_document | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_update_with_embedding | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_delete_document | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_list_default | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_list_with_limit | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_list_with_filter | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_list_empty_collection | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_table_output | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_create_invalid_json | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_cross_collection | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_update_nonexistent | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_crud_create_with_special_chars | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_create_basic | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_create_with_metadata | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_list_all | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_list_active_only | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_list_by_type | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_get_by_id | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_get_conversations | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_update_title | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_close | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_close_already_closed | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_current | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_table_output | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_invalid_id | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_list_with_limit | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_episode_create_invalid_metadata | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_add_relationship | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_add_duplicate_relationship | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_outbound | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_inbound | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_any_direction | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_with_filter | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_visualize | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_delete_relationship | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_traverse_nonexistent_node | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_table_output | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_add_relationship_invalid_type | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_stats | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_subgraph | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_create_basic | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_create_with_metadata | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_list_default | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_list_with_limit | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_list_by_conversation | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_search_basic | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_search_with_threshold | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_get_by_id | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_get_invalid_id | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_history_recent | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_history_by_conversation | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_history_with_limit | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_table_output | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_create_with_entities | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_memory_search_empty_results | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_bm25_search_default | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_bm25_search_custom_collection | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_semantic_search_default | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_semantic_search_with_threshold | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_semantic_search_with_tags | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_keyword_search | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_tag_search_single_tag | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_tag_search_multiple_tags_any | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_tag_search_multiple_tags_all | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_graph_search | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_search_with_limit | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_search_table_output | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_search_error_handling | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_search_empty_query | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_init | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_adjacency_matrix | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_modularity | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_small_community_merging | 16:48:57 | 0.000s | ⚠️ ERROR |
| test_empty_graph | 16:48:57 | 0.000s | ⚠️ ERROR |

---

**Report Generation**: Automated via ArangoDB Memory Bank Test Reporter  
**Compliance**: Task List Template Guide v2 Compatible  
**Non-Hallucinated Results**: All data sourced from actual test execution and ArangoDB queries  
