__author__	= "Michael E. Cotterell"
__email__	 = "mepcotterell@gmail.com"
__copyright__ = "Copyright 2013, Michael E. Cotterell"
__license__   = "MIT"

import imp
import os
import logging
import collections

logging.basicConfig(level = logging.DEBUG)

class PluginManager:
	'''
	A simple plugin manager
	'''

	def __init__(self, plugin_folder, main_module = '__init__', log = logging):
		self.logging		= log
		self.plugin_folder  = plugin_folder
		self.main_module	= main_module
		self.loaded_plugins = collections.OrderedDict({})

	def get_available_plugins(self):
		''' 
		Returns a dictionary of plugins available in the plugin folder
		'''
		plugins = {}
		for possible in os.listdir(self.plugin_folder):
			location = os.path.join(self.plugin_folder, possible)
			if os.path.isdir(location) and self.main_module + '.py' in os.listdir(location):
				info = imp.find_module(self.main_module, [location])
				plugins[possible] = {
					'name': possible, 
					'info': info
				}
		return plugins

	def get_loaded_plugins(self):
		'''
		Returns a dictionary of the loaded plugin modules
		'''
		return self.loaded_plugins.copy()

	def init_plugin(self, plugin_name, rself=None):
		module = self.loaded_plugins[plugin_name]['module']
		hook_func_name = 'init_%s' %plugin_name
		if hasattr(module, hook_func_name):
			hook_func = getattr(module, hook_func_name)
			hook_params = {'self': rself}
			rself = hook_func(hook_params)
			return rself

	def load_plugin(self, plugin_name):
		'''
		Loads a plugin module
		'''
		plugins = self.get_available_plugins()
		if plugin_name in plugins:
			if plugin_name not in self.loaded_plugins:
				module = imp.load_module(self.main_module, *plugins[plugin_name]['info'])
				self.loaded_plugins[plugin_name] = {
					'name': plugin_name, 
					'info': plugins[plugin_name]['info'], 
					'module': module
				}
				self.logging.info('plugin "%s" loaded' % plugin_name)
			else:
				self.logging.warn('plugin "%s" already loaded' % plugin_name)
		else:
			self.logging.error('cannot locate plugin "%s"' % plugin_name)
			raise Exception('cannot locate plugin "%s"' % plugin_name)

	def unload_plugin(self, plugin_name):
		'''
		Unloads a plugin module
		'''
		del self.loaded_plugins[plugin_name]
		self.logging.info('plugin "%s" unloaded' % plugin_name)

	def execute_event_hook(self, hook_name, hook_params = {}):
		'''
		Executes event hook functions of the form action_hook_name contained in
		the loaded plugin modules.
		'''
		res = None
		for key, plugin_info in self.loaded_plugins.items():
			module = plugin_info['module']
			hook_func_name = 'event_%s' % hook_name
			if hasattr(module, hook_func_name):
				hook_func = getattr(module, hook_func_name)
				res = hook_func(hook_params)
				break
		return res

	def execute_action_hook(self, hook_name, hook_params = {}):
		'''
		Executes action hook functions of the form action_hook_name contained in
		the loaded plugin modules.
		'''
		res = None
		for key, plugin_info in self.loaded_plugins.items():
			module = plugin_info['module']
			hook_func_name = 'action_%s' % hook_name
			if hasattr(module, hook_func_name):
				hook_func = getattr(module, hook_func_name)
				res = hook_func(hook_params)
				break
		return res

	def execute_filter_hook(self, hook_name, hook_params = {}):
		'''
		Filters the hook_params through filter hook functions of the form 
		filter_hook_name contained in the loaded plugin modules.
		'''
		hook_params_keys = hook_params.keys()
		for key, plugin_info in self.loaded_plugins.items():
			module = plugin_info['module']
			hook_func_name = 'filter_%s' % hook_name
			if hasattr(module, hook_func_name):
				hook_func   = getattr(module, hook_func_name)
				hook_params = hook_func(hook_params)
				for nkey in hook_params_keys:
					if nkey not in hook_params.keys():
						msg = 'function "%s" in plugin "%s" is missing "%s" in the dict it returns' % (hook_func_name, plugin_info['name'], nkey)
						self.logging.error(msg)
						raise Exception(msg)
		return hook_params
