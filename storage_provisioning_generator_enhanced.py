#!/usr/bin/env python3
"""
Enhanced Storage Provisioning Generator
Reads all_storage_facts.json and generates Ansible playbooks for:
- Creating all LDEVs from storage facts
- Creating all Hostgroups from storage facts
- Provisioning LDEVs to appropriate hostgroups based on mappings
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

class StorageProvisioningGenerator:
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.data = None
        self.ldevs = []
        self.hostgroups = []
        self.ldev_hg_mappings = {}
        self.load_facts()
    
    def load_facts(self):
        """Load storage facts from JSON file"""
        try:
            with open(self.json_file, 'r') as f:
                self.data = json.load(f)
            print(f"✓ Loaded storage facts from {self.json_file}")
        except Exception as e:
            print(f"✗ Error loading JSON: {e}")
            exit(1)
    
    def extract_ldevs(self) -> List[Dict[str, Any]]:
        """Extract all LDEVs from storage facts"""
        if 'ldevs' not in self.data:
            return []
        
        ldevs_data = self.data['ldevs'].get('ansible_facts', {}).get('volumes', [])
        
        # Process LDEVs and build mapping
        for ldev in ldevs_data:
            ldev_id = ldev.get('ldev_id')
            if ldev.get('hostgroups'):
                self.ldev_hg_mappings[ldev_id] = ldev['hostgroups']
        
        self.ldevs = ldevs_data
        return ldevs_data
    
    def extract_hostgroups(self) -> List[Dict[str, Any]]:
        """Extract all Hostgroups from storage facts"""
        if 'host_groups' not in self.data:
            return []
        
        hgs_data = self.data['host_groups'].get('ansible_facts', {}).get('hostGroups', [])
        self.hostgroups = hgs_data
        return hgs_data
    
    def generate_ldev_playbook(self) -> str:
        """Generate playbook to create all LDEVs"""
        ldevs = self.extract_ldevs()
        
        # Build LDEV config list
        ldev_configs = []
        for ldev in ldevs:
            ldev_configs.append({
                'ldev_id': ldev.get('ldev_id'),
                'name': ldev.get('name'),
                'size': ldev.get('total_capacity'),
                'pool_id': ldev.get('pool_id'),
                'emulation_type': ldev.get('emulation_type'),
                'capacity_saving': ldev.get('deduplication_compression_mode', 'compression_deduplication'),
                'data_reduction_share': ldev.get('is_data_reduction_share_enabled', True)
            })
        
        playbook = f"""---
####################################################################
# Auto-Generated LDEV Creation Playbook - All LDEVs
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Total LDEVs: {len(ldev_configs)}
####################################################################
- name: Create All Logical Devices (LDEVs)
  hosts: localhost
  gather_facts: false

  vars_files:
    - ../ansible_vault_vars/ansible_vault_storage_var.yml

  vars:
    connection_info:
      address: "{{{{ storage_address }}}}"
      username: "{{{{ vault_storage_username }}}}"
      password: "{{{{ vault_storage_secret }}}}"
    
    # LDEV Configuration extracted from all_storage_facts.json
    ldev_config:
"""
        
        # Add each LDEV config
        for ldev in ldev_configs:
            playbook += f"""      - ldev_id: {ldev['ldev_id']}
        name: "{ldev['name']}"
        size: "{ldev['size']}"
        pool_id: {ldev['pool_id']}
        emulation_type: "{ldev['emulation_type']}"
        capacity_saving: "{ldev['capacity_saving']}"
        data_reduction_share: {str(ldev['data_reduction_share']).lower()}
"""
        
        playbook += f"""
  tasks:
    ####################################################################
    # Task: Create All LDEVs
    ####################################################################
    - name: Create All LDEVs from storage facts
      hitachivantara.vspone_block.vsp.hv_ldev:
        connection_info: "{{ connection_info }}"
        state: present
        spec:
          pool_id: "{{ item.pool_id }}"
          size: "{{ item.size }}"
          name: "{{ item.name }}"
          capacity_saving: "{{ item.capacity_saving }}"
          data_reduction_share: "{{ item.data_reduction_share }}"
      register: ldev_result
      loop: "{{ ldev_config }}"
      loop_control:
        label: "LDEV {{ item.ldev_id }}: {{ item.name }}"
      tags:
        - ldev
        - always

    - name: Debug LDEV creation results
      ansible.builtin.debug:
        msg: "Created LDEV {{ item.result.volume.ldev_id }} - {{ item.result.volume.name }}"
      loop: "{{ ldev_result.results }}"
      loop_control:
        label: "{{ item.item.name }}"
      when: item is succeeded

    - name: Collect created LDEV IDs
      ansible.builtin.set_fact:
        created_ldev_ids: "{{ ldev_result.results | map(attribute='result.volume.ldev_id') | list }}"
      when: ldev_result is succeeded

  post_tasks:
    - name: Display created LDEVs information
      ansible.builtin.debug:
        msg: |
          ✓ LDEVs Created Successfully!
          Total LDEVs Created: {{ ldev_config | length }}
          Created LDEV IDs: {{ created_ldev_ids | default([]) }}
"""
        
        return playbook
    
    def generate_hostgroup_playbook(self) -> str:
        """Generate playbook to create all Hostgroups"""
        hostgroups = self.extract_hostgroups()
        
        # Build hostgroup config list
        hg_configs = []
        for hg in hostgroups:
            hg_configs.append({
                'hg_id': hg.get('host_group_id'),
                'name': hg.get('host_group_name'),
                'port': hg.get('port_id'),
                'host_mode': hg.get('host_mode'),
                'host_mode_options': hg.get('host_mode_options', []),
                'wwns': hg.get('wwns', [])
            })
        
        playbook = f"""---
####################################################################
# Auto-Generated Hostgroup Creation Playbook - All Hostgroups
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Total Hostgroups: {len(hg_configs)}
####################################################################
- name: Create All Hostgroups
  hosts: localhost
  gather_facts: false

  vars_files:
    - ../ansible_vault_vars/ansible_vault_storage_var.yml

  vars:
    connection_info:
      address: "{{{{ storage_address }}}}"
      username: "{{{{ vault_storage_username }}}}"
      password: "{{{{ vault_storage_secret }}}}"
    
    # Hostgroup Configuration extracted from all_storage_facts.json
    hostgroup_config:
"""
        
        # Add each hostgroup config
        for hg in hg_configs:
            playbook += f"""      - hg_id: {hg['hg_id']}
        name: "{hg['name']}"
        port: "{hg['port']}"
        host_mode: "{hg['host_mode']}"
        host_mode_options: {hg['host_mode_options']}
        wwns: {hg['wwns']}
"""
        
        playbook += f"""
  tasks:
    ####################################################################
    # Task: Create All Hostgroups
    ####################################################################
    - name: Create All Hostgroups from storage facts
      hitachivantara.vspone_block.vsp.hv_hg:
        connection_info: "{{ connection_info }}"
        state: present
        spec:
          name: "{{ item.name }}"
          port: "{{ item.port }}"
          host_mode: "{{ item.host_mode }}"
      register: hostgroup_result
      loop: "{{ hostgroup_config }}"
      loop_control:
        label: "HG {{ item.hg_id }}: {{ item.name }} on {{ item.port }}"
      tags:
        - hostgroup
        - always

    - name: Debug hostgroup creation results
      ansible.builtin.debug:
        msg: "Created Hostgroup {{ item.item.hg_id }} - {{ item.item.name }} on {{ item.item.port }}"
      loop: "{{ hostgroup_result.results }}"
      loop_control:
        label: "{{ item.item.name }}"
      when: item is succeeded

    ####################################################################
    # Task: Add WWNs to Hostgroups (if any exist)
    ####################################################################
    - name: Add WWNs to Hostgroups
      hitachivantara.vspone_block.vsp.hv_hg:
        connection_info: "{{ connection_info }}"
        state: present
        spec:
          state: add_wwn
          name: "{{ item.name }}"
          port: "{{ item.port }}"
          wwns: "{{ item.wwns }}"
      loop: "{{ hostgroup_config }}"
      loop_control:
        label: "{{ item.name }}"
      when: 
        - item.wwns | length > 0
      tags:
        - hostgroup
        - wwn

    - name: Collect created hostgroup information
      ansible.builtin.set_fact:
        created_hostgroups: "{{ hostgroup_result.results | map(attribute='item') | list }}"
      when: hostgroup_result is succeeded

  post_tasks:
    - name: Display created hostgroups information
      ansible.builtin.debug:
        msg: |
          ✓ Hostgroups Created Successfully!
          Total Hostgroups Created: {{ hostgroup_config | length }}
"""
        
        return playbook
    
    def generate_provision_playbook(self) -> str:
        """Generate playbook to provision LDEVs to hostgroups based on actual mappings"""
        self.extract_ldevs()
        self.extract_hostgroups()
        
        # Build provisioning tasks based on actual LDEV-HG mappings
        provisioning_tasks = []
        
        for ldev_id, hg_list in self.ldev_hg_mappings.items():
            # Find LDEV name
            ldev_name = next((l['name'] for l in self.ldevs if l['ldev_id'] == ldev_id), f"LDEV-{ldev_id}")
            
            for hg_mapping in hg_list:
                hg_name = hg_mapping.get('name')
                hg_port = hg_mapping.get('port_id')
                
                provisioning_tasks.append({
                    'ldev_id': ldev_id,
                    'ldev_name': ldev_name,
                    'hg_name': hg_name,
                    'hg_port': hg_port
                })
        
        playbook = f"""---
####################################################################
# Auto-Generated LDEV Provisioning to Hostgroups Playbook
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Total LDEV-HG Mappings: {len(provisioning_tasks)}
####################################################################
- name: Provision All LDEVs to Hostgroups
  hosts: localhost
  gather_facts: false

  vars_files:
    - ../ansible_vault_vars/ansible_vault_storage_var.yml

  vars:
    connection_info:
      address: "{{{{ storage_address }}}}"
      username: "{{{{ vault_storage_username }}}}"
      password: "{{{{ vault_storage_secret }}}}"
    
    # LDEV to Hostgroup Provisioning Mappings from all_storage_facts.json
    provisioning_mappings:
"""
        
        # Add each provisioning mapping
        for task in provisioning_tasks:
            playbook += f"""      - ldev_id: {task['ldev_id']}
        ldev_name: "{task['ldev_name']}"
        hostgroup_name: "{task['hg_name']}"
        port: "{task['hg_port']}"
"""
        
        playbook += f"""
  tasks:
    ####################################################################
    # Task: Provision LDEVs to Hostgroups
    ####################################################################
    - name: Provision LDEVs to Hostgroups
      hitachivantara.vspone_block.vsp.hv_hg:
        connection_info: "{{ connection_info }}"
        state: present
        spec:
          state: present_ldev
          name: "{{ item.hostgroup_name }}"
          port: "{{ item.port }}"
          ldevs: ["{{ item.ldev_id }}"]
      register: provision_result
      loop: "{{ provisioning_mappings }}"
      loop_control:
        label: "LDEV {{ item.ldev_id }} ({{ item.ldev_name }}) -> {{ item.hostgroup_name }} on {{ item.port }}"
      tags:
        - provision
        - always

    - name: Debug provisioning results
      ansible.builtin.debug:
        msg: "Provisioned LDEV {{ item.item.ldev_id }} to {{ item.item.hostgroup_name }}"
      loop: "{{ provision_result.results }}"
      loop_control:
        label: "{{ item.item.ldev_name }} -> {{ item.item.hostgroup_name }}"
      when: item is succeeded

  post_tasks:
    - name: Display provisioning summary
      ansible.builtin.debug:
        msg: |
          ✓ LDEVs Provisioned Successfully!
          Total Mappings: {{ provisioning_mappings | length }}
          Successful: {{ provision_result.results | selectattr('is_succeeded') | length }}
          Failed: {{ provision_result.results | selectattr('failed', 'true') | length }}
"""
        
        return playbook
    
    def generate_combined_workflow(self) -> str:
        """Generate combined playbook with all three tasks"""
        self.extract_ldevs()
        self.extract_hostgroups()
        
        # Build LDEV config
        ldev_configs = []
        for ldev in self.ldevs:
            ldev_configs.append({
                'ldev_id': ldev.get('ldev_id'),
                'name': ldev.get('name'),
                'size': ldev.get('total_capacity'),
                'pool_id': ldev.get('pool_id'),
                'capacity_saving': ldev.get('deduplication_compression_mode', 'compression_deduplication'),
                'data_reduction_share': ldev.get('is_data_reduction_share_enabled', True)
            })
        
        # Build hostgroup config
        hg_configs = []
        for hg in self.hostgroups:
            hg_configs.append({
                'hg_id': hg.get('host_group_id'),
                'name': hg.get('host_group_name'),
                'port': hg.get('port_id'),
                'host_mode': hg.get('host_mode'),
                'host_mode_options': hg.get('host_mode_options', []),
                'wwns': hg.get('wwns', [])
            })
        
        # Build provisioning mappings
        provisioning_tasks = []
        for ldev_id, hg_list in self.ldev_hg_mappings.items():
            ldev_name = next((l['name'] for l in self.ldevs if l['ldev_id'] == ldev_id), f"LDEV-{ldev_id}")
            for hg_mapping in hg_list:
                provisioning_tasks.append({
                    'ldev_id': ldev_id,
                    'ldev_name': ldev_name,
                    'hg_name': hg_mapping.get('name'),
                    'hg_port': hg_mapping.get('port_id')
                })
        
        playbook = f"""---
####################################################################
# Auto-Generated Complete Provisioning Workflow
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# LDEVs: {len(ldev_configs)}, Hostgroups: {len(hg_configs)}, Mappings: {len(provisioning_tasks)}
####################################################################
- name: Complete Storage Provisioning Workflow
  hosts: localhost
  gather_facts: false

  vars_files:
    - ../ansible_vault_vars/ansible_vault_storage_var.yml

  vars:
    connection_info:
      address: "{{{{ storage_address }}}}"
      username: "{{{{ vault_storage_username }}}}"
      password: "{{{{ vault_storage_secret }}}}"
    
    # All LDEVs from all_storage_facts.json
    ldev_config:
"""
        
        # Add LDEV configs
        for ldev in ldev_configs:  # Include all LDEVs
            playbook += f"""      - ldev_id: {ldev['ldev_id']}
        name: "{ldev['name']}"
        size: "{ldev['size']}"
        pool_id: {ldev['pool_id']}
"""
        
        
        playbook += f"""
    # All Hostgroups from all_storage_facts.json
    hostgroup_config:
"""
        
        # Add hostgroup configs
        for hg in hg_configs:  # Include all hostgroups
            playbook += f"""      - hg_id: {hg['hg_id']}
        name: "{hg['name']}"
        port: "{hg['port']}"
        host_mode: "{hg['host_mode']}"
"""
        
        
        playbook += f"""
    # LDEV-Hostgroup Provisioning Mappings
    provisioning_mappings:
"""
        
        # Add provisioning mappings
        for task in provisioning_tasks:  # Include all mappings
            playbook += f"""      - ldev_id: {task['ldev_id']}
        ldev_name: "{task['ldev_name']}"
        hostgroup_name: "{task['hg_name']}"
        port: "{task['hg_port']}"
"""
        
        
        playbook += f"""

  tasks:
    ####################################################################
    # Step 1: Create All LDEVs
    ####################################################################
    - name: Create All LDEVs from storage facts
      hitachivantara.vspone_block.vsp.hv_ldev:
        connection_info: "{{ connection_info }}"
        state: present
        spec:
          pool_id: "{{ item.pool_id }}"
          size: "{{ item.size }}"
          name: "{{ item.name }}"
      register: ldev_result
      loop: "{{ ldev_config }}"
      loop_control:
        label: "LDEV {{ item.ldev_id }}: {{ item.name }}"
      tags:
        - ldev
        - always

    - name: Collect LDEV creation results
      ansible.builtin.set_fact:
        created_ldevs: "{{ ldev_result.results | map(attribute='item') | list }}"
      when: ldev_result is succeeded

    ####################################################################
    # Step 2: Create All Hostgroups
    ####################################################################
    - name: Create All Hostgroups from storage facts
      hitachivantara.vspone_block.vsp.hv_hg:
        connection_info: "{{ connection_info }}"
        state: present
        spec:
          name: "{{ item.name }}"
          port: "{{ item.port }}"
          host_mode: "{{ item.host_mode }}"
      register: hostgroup_result
      loop: "{{ hostgroup_config }}"
      loop_control:
        label: "HG {{ item.hg_id }}: {{ item.name }} on {{ item.port }}"
      tags:
        - hostgroup
        - always

    - name: Collect Hostgroup creation results
      ansible.builtin.set_fact:
        created_hostgroups: "{{ hostgroup_result.results | map(attribute='item') | list }}"
      when: hostgroup_result is succeeded

    ####################################################################
    # Step 3: Provision LDEVs to Hostgroups
    ####################################################################
    - name: Provision LDEVs to Hostgroups
      hitachivantara.vspone_block.vsp.hv_hg:
        connection_info: "{{ connection_info }}"
        state: present
        spec:
          state: present_ldev
          name: "{{ item.hostgroup_name }}"
          port: "{{ item.port }}"
          ldevs: ["{{ item.ldev_id }}"]
      register: provision_result
      loop: "{{ provisioning_mappings }}"
      loop_control:
        label: "LDEV {{ item.ldev_id }} -> {{ item.hostgroup_name }}"
      tags:
        - provision
        - always

  post_tasks:
    - name: Display Provisioning Summary
      ansible.builtin.debug:
        msg: |
          ╔════════════════════════════════════════════════════════════╗
          ║           STORAGE PROVISIONING WORKFLOW COMPLETE           ║
          ╚════════════════════════════════════════════════════════════╝
          
          ✓ LDEVs Created: {{ ldev_config | length }}
          ✓ Hostgroups Created: {{ hostgroup_config | length }}
          ✓ LDEV-HG Mappings: {{ provisioning_mappings | length }}
          
          Execution Status:
          - LDEV Creation: {{ ldev_result.results | selectattr('is_succeeded') | length }} successful
          - Hostgroup Creation: {{ hostgroup_result.results | selectattr('is_succeeded') | length }} successful
          - LDEV Provisioning: {{ provision_result.results | selectattr('is_succeeded') | length }} successful
"""
        
        return playbook
    
    def generate_all(self):
        """Generate all playbooks"""
        output_dir = Path('generated_playbooks')
        output_dir.mkdir(exist_ok=True)
        
        print("\n" + "="*80)
        print("Storage Provisioning Playbook Generator (Enhanced)")
        print("="*80)
        
        # Extract data
        self.extract_ldevs()
        self.extract_hostgroups()
        
        print(f"\n✓ Found {len(self.ldevs)} LDEVs")
        print(f"✓ Found {len(self.hostgroups)} Hostgroups")
        print(f"✓ Found {len(self.ldev_hg_mappings)} LDEV-HG Mappings")
        
        # Generate playbooks
        playbooks = {
            '03_create_ldevs_all.yml': self.generate_ldev_playbook(),
            '04_create_hostgroups_all.yml': self.generate_hostgroup_playbook(),
            '05_provision_ldevs_to_hostgroups_all.yml': self.generate_provision_playbook(),
            '00_complete_provisioning_workflow_enhanced.yml': self.generate_combined_workflow()
        }
        
        for filename, content in playbooks.items():
            filepath = output_dir / filename
            with open(filepath, 'w') as f:
                f.write(content)
            size = len(content) / 1024
            print(f"✓ Generated: {filepath} ({size:.1f} KB)")
        
        print("\n" + "="*80)
        print("Summary")
        print("="*80)
        print(f"Total LDEVs to create: {len(self.ldevs)}")
        print(f"Total Hostgroups to create: {len(self.hostgroups)}")
        print(f"Total LDEV-HG Mappings: {len(self.ldev_hg_mappings)}")
        print(f"\nAll playbooks saved to: {output_dir}")
        print("="*80 + "\n")

if __name__ == '__main__':
    generator = StorageProvisioningGenerator('all_storage_facts.json')
    generator.generate_all()
