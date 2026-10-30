import json
import sys
import types
from unittest.mock import Mock

import requests
from hermes_fxmacrodata import plugin
from hermes_fxmacrodata.public_client import list_operations
from transport_fixtures import Transport, arguments


def test_all_current_tools_registered_without_network():
    context=Mock()
    plugin.register(context)
    operations=list_operations()
    assert len(operations)==98
    calls=context.register_tool.call_args_list
    assert len(calls)==100
    schemas={c.kwargs['name']:c.kwargs['schema'] for c in calls}
    for operation in operations:
        assert schemas['fxmd_'+operation.name]['parameters']==operation.input_schema


def test_optional_secret_uses_host_profile_and_ignores_process(monkeypatch):
    monkeypatch.setenv('FXMACRODATA_API_KEY','wrong-profile-synthetic')
    host=types.ModuleType('agent.secret_scope')
    host.get_secret=Mock(return_value='active-profile-synthetic')
    monkeypatch.setitem(sys.modules,'agent.secret_scope',host)
    assert plugin.profile_key()=='active-profile-synthetic'
    host.get_secret.assert_called_once_with('FXMACRODATA_API_KEY','')
    host.get_secret.return_value=None
    try:
        plugin.profile_key()
    except Exception:
        pass  # Invalid host value must fail; it cannot use the process key.
    else:
        raise AssertionError('Invalid profile credential was accepted')


def test_research_post_preserves_public_body(monkeypatch):
    transport=Transport()
    monkeypatch.setattr(requests.Session,'request',lambda session,method,url,**kw:transport.request(session,method,url,**kw))
    operation=next(o for o in list_operations() if o.name=='research_panel')
    raw=arguments(operation)
    with plugin.FXMacroDataClient(api_key='synthetic') as client:
        client.execute('research_panel',raw)
    method,url,kwargs=transport.calls[0]
    assert method=='POST' and url.endswith('/v1/research/panel')
    assert kwargs['json']==raw['body']


def test_all_native_handlers_use_refreshed_operations(monkeypatch):
    monkeypatch.setattr(plugin,'profile_key',lambda:'')
    transport=Transport()
    monkeypatch.setattr(requests.Session,'request',lambda session,method,url,**kw:transport.request(session,method,url,**kw))
    context=Mock();context.get_config.return_value=30
    plugin.register(context)
    handlers={c.kwargs['name']:c.kwargs['handler'] for c in context.register_tool.call_args_list}
    for operation in list_operations():
        output=json.loads(handlers['fxmd_'+operation.name](arguments(operation)))
        assert 'error' not in output,(operation.name,output)
