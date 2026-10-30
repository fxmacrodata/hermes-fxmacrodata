# Native coverage — 0.3.0



100 tools: 41 public REST operations, 57 MCP tools, USD brief and atomic history snapshot. The reviewed catalogue may retain the prior pin until the update is accepted.



| Tool | Contract |

|---|---|

| `fxmd_health` | GET /v1/health |

| `fxmd_ping` | GET /v1/ping |

| `fxmd_forex` | GET /v1/forex/{base}/{quote} |

| `fxmd_reference_rates` | GET /v1/fx/reference-rates/{base}/{quote} |

| `fxmd_intraday_reference_rates` | GET /v1/fx/intraday-reference-rates/{base}/{quote} |

| `fxmd_session_rates` | GET /v1/fx/session-rates/{base}/{quote} |

| `fxmd_fx_sources` | GET /v1/fx/sources |

| `fxmd_fx_source_universe` | GET /v1/fx/source-universe |

| `fxmd_research_panel` | POST /v1/research/panel |

| `fxmd_data_catalogue` | GET /v1/data_catalogue/{currency} |

| `fxmd_release_calendar` | GET /v1/calendar/{currency} |

| `fxmd_calendar_snapshot` | GET /v1/calendar/{currency}/snapshot |

| `fxmd_calendar_versions` | GET /v1/calendar/{currency}/events/{archive_event_id}/versions |

| `fxmd_calendar_archive_coverage` | GET /v1/calendar/{currency}/coverage |

| `fxmd_market_sessions` | GET /v1/market_sessions |

| `fxmd_rate_differentials` | GET /v1/rate_differentials/{base}/{quote} |

| `fxmd_curves` | GET /v1/curves/{currency} |

| `fxmd_financial_prices` | GET /v1/financial_prices/{currency} |

| `fxmd_native_sources` | GET /v1/native |

| `fxmd_native_history` | GET /v1/native/{source} |

| `fxmd_positioning_sources` | GET /v1/positioning |

| `fxmd_positioning_history` | GET /v1/positioning/{instrument} |

| `fxmd_press_releases` | GET /v1/press-releases/{currency} |

| `fxmd_risk_sentiment_changes` | GET /v1/risk_sentiment/changes |

| `fxmd_risk_sentiment` | GET /v1/risk_sentiment |

| `fxmd_factors` | GET /v1/factors/{currency}/{factor} |

| `fxmd_prediction_coverage_index` | GET /v1/predictions/coverage |

| `fxmd_prediction_coverage_for_currency` | GET /v1/predictions/coverage/{currency} |

| `fxmd_predictions_missing_indicator` | GET /v1/predictions/{currency} |

| `fxmd_event_predictions` | GET /v1/predictions/{currency}/{indicator} |

| `fxmd_latest_announcements` | GET /v1/announcements/{currency}/latest |

| `fxmd_indicator_history` | GET /v1/announcements/{currency}/{indicator} |

| `fxmd_cot` | GET /v1/cot/{currency} |

| `fxmd_latest_commodities` | GET /v1/commodities/latest |

| `fxmd_commodities` | GET /v1/commodities/{indicator} |

| `fxmd_list_settlement_contracts` | GET /v1/settlement/contracts |

| `fxmd_settlement_keys` | GET /v1/settlement/keys |

| `fxmd_settle_contract` | GET /v1/settlement/contracts/{contract_id} |

| `fxmd_settle_series` | GET /v1/settlement/{currency}/{indicator} |

| `fxmd_announcement_changes` | GET /v1/announcements/changes |

| `fxmd_stream_events` | GET /v1/stream/events |

| `fxmd_mcp_ping` | MCP /mcp |

| `fxmd_mcp_mcp_capabilities` | MCP /mcp |

| `fxmd_mcp_mcp_auth_guide` | MCP /mcp |

| `fxmd_mcp_subscribe_for_mcp_access` | MCP /mcp |

| `fxmd_mcp_data_catalogue` | MCP /mcp |

| `fxmd_mcp_source_metadata` | MCP /mcp |

| `fxmd_mcp_risk_sentiment` | MCP /mcp |

| `fxmd_mcp_risk_sentiment_changes` | MCP /mcp |

| `fxmd_mcp_macro_news` | MCP /mcp |

| `fxmd_mcp_release_calendar` | MCP /mcp |

| `fxmd_mcp_calendar_snapshot` | MCP /mcp |

| `fxmd_mcp_calendar_event_versions` | MCP /mcp |

| `fxmd_mcp_calendar_archive_coverage` | MCP /mcp |

| `fxmd_mcp_release_calendar_visual_artifact` | MCP /mcp |

| `fxmd_mcp_event_predictions` | MCP /mcp |

| `fxmd_mcp_latest_announcements` | MCP /mcp |

| `fxmd_mcp_announcement_changes` | MCP /mcp |

| `fxmd_mcp_press_releases` | MCP /mcp |

| `fxmd_mcp_macro_factor` | MCP /mcp |

| `fxmd_mcp_fx_reference_sources` | MCP /mcp |

| `fxmd_mcp_fx_reference_universe` | MCP /mcp |

| `fxmd_mcp_fx_intraday_reference_rates` | MCP /mcp |

| `fxmd_mcp_rate_curve` | MCP /mcp |

| `fxmd_mcp_rate_differentials` | MCP /mcp |

| `fxmd_mcp_latest_commodities` | MCP /mcp |

| `fxmd_mcp_forex` | MCP /mcp |

| `fxmd_mcp_seasonality` | MCP /mcp |

| `fxmd_mcp_indicator_query` | MCP /mcp |

| `fxmd_mcp_plot_visual_artifact` | MCP /mcp |

| `fxmd_mcp_indicator_visual_artifact` | MCP /mcp |

| `fxmd_mcp_forex_visual_artifact` | MCP /mcp |

| `fxmd_mcp_commodities_visual_artifact` | MCP /mcp |

| `fxmd_mcp_cot_visual_artifact` | MCP /mcp |

| `fxmd_mcp_policy_rate_differential_visual_artifact` | MCP /mcp |

| `fxmd_mcp_macro_briefing_task` | MCP /mcp |

| `fxmd_mcp_indicator_intel_task` | MCP /mcp |

| `fxmd_mcp_pair_intel_task` | MCP /mcp |

| `fxmd_mcp_macro_heatmap_task` | MCP /mcp |

| `fxmd_mcp_policy_scenario_modeler_task` | MCP /mcp |

| `fxmd_mcp_macro_war_room_task` | MCP /mcp |

| `fxmd_mcp_event_impact_replay_task` | MCP /mcp |

| `fxmd_mcp_quant_scenario_lab_task` | MCP /mcp |

| `fxmd_mcp_known_at_time_task` | MCP /mcp |

| `fxmd_mcp_macro_regime_classifier_task` | MCP /mcp |

| `fxmd_mcp_release_risk_score_task` | MCP /mcp |

| `fxmd_mcp_portfolio_risk_engine_task` | MCP /mcp |

| `fxmd_mcp_fx_trade_setup_task` | MCP /mcp |

| `fxmd_mcp_fx_backtest_task` | MCP /mcp |

| `fxmd_mcp_macro_research_pack_task` | MCP /mcp |

| `fxmd_mcp_prediction_coverage` | MCP /mcp |

| `fxmd_mcp_market_sessions` | MCP /mcp |

| `fxmd_mcp_cot_data` | MCP /mcp |

| `fxmd_mcp_commodities` | MCP /mcp |

| `fxmd_mcp_positioning` | MCP /mcp |

| `fxmd_mcp_native_history` | MCP /mcp |

| `fxmd_mcp_financial_prices` | MCP /mcp |

| `fxmd_mcp_official_dataset_family` | MCP /mcp |

| `fxmd_usd_macro_brief` | composed REST composed |

| `fxmd_indicator_history_snapshot` | composed REST composed |



SSE capture is finite; no background listener. Interactive MCP Apps are preserved as data, not rendered. The host provides models separately. Schema snapshots do not establish production data correctness.

