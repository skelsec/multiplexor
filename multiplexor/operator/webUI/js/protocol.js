

var OperatorCmdType = {
	LIST_AGENTS : 0,
	LIST_AGENTS_RPLY : 1,
	GET_AGENT_INFO : 2,
	GET_AGENT_INFO_RPLY : 3,
	GET_PLUGINS : 4,
	GET_PLUGINS_RPLY : 5,
	GET_PLUGIN_INFO : 6,
	GET_PLUGIN_INFO_RPLY : 7,
	START_PLUGIN : 8,
	PLUGIN_STARTED : 9,
	PLUGIN_STOPPED : 10,
};
	

var operatorListAgentsCmd = {'cmdtype':OperatorCmdType.LIST_AGENTS} ;
var operatorGetAgentInfoCmd = {'cmdtype':OperatorCmdType.GET_AGENT_INFO, 'agent_id': null};
var operatorGetPluginsCmd = {'cmdtype':OperatorCmdType.GET_PLUGINS, 'agent_id': null};
var operatorGetPluginInfoCmd = {'cmdtype':OperatorCmdType.GET_PLUGIN_INFO, 'agent_id': null, 'plugin_id': null};
var operatorStartPluginCmd = {'cmdtype':OperatorCmdType.START_PLUGIN, 'agent_id': null, 'plugin_type': null, 'plugin_data': null};
