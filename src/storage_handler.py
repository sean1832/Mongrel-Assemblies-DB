import streamlit as st
import paramiko
from paramiko import RSAKey
import base64
from contextlib import contextmanager

ip = st.secrets["sftp"]["host"]
username = st.secrets["sftp"]["username"]
password = st.secrets["sftp"]["password"]
port = st.secrets["sftp"]["port"]
key_data = st.secrets["sftp"]["key_data"]


# --------------------------------------------

@contextmanager
def create_ssh_client(ip, port, username, password):
    client = paramiko.SSHClient()
    ssh_host_key = RSAKey(data=base64.b64decode(key_data.encode()))
    client.get_host_keys().add(ip, 'ssh-rsa', ssh_host_key)
    client.connect(ip, port, username, password)
    try:
        yield client
    finally:
        client.close()


@contextmanager
def create_sftp_client(ssh_client):
    sftp_client = ssh_client.open_sftp()
    try:
        yield sftp_client
    finally:
        sftp_client.close()


def upload_file(filename, local_dir, remote_dir):
    """Upload file from local machine to remote server"""
    with create_ssh_client(ip, port, username, password) as ssh_client:
        with create_sftp_client(ssh_client) as sftp_client:
            remote_full_path = f"{remote_dir}/{filename}"
            local_full_path = f"{local_dir}/{filename}"
            sftp_client.put(local_full_path, remote_full_path)


def download_file(filename, remote_dir, local_dir):
    """Download file from remote server to local machine"""
    with create_ssh_client(ip, port, username, password) as ssh_client:
        with create_sftp_client(ssh_client) as sftp_client:
            remote_full_path = f"{remote_dir}/{filename}"
            local_full_path = f"{local_dir}/{filename}"
            sftp_client.get(remote_full_path, local_full_path)

