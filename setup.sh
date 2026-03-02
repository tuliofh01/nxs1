#!/bin/bash
set -e

SSH_GROUP="ssh-users"

echo "Checking for SSH group..."
if ! getent group "$SSH_GROUP" >/dev/null; then
    echo "Creating SSH group: $SSH_GROUP"
    sudo groupadd "$SSH_GROUP"
else
    echo "SSH group exists: $SSH_GROUP"
fi

echo "Listing users in SSH group..."
getent group "$SSH_GROUP" | cut -d: -f4

read -p "Do you want to add a user to this group? (y/n): " ADD_USER
if [[ "$ADD_USER" == "y" ]]; then
    read -p "Enter username to add: " USER_NAME
    if id "$USER_NAME" >/dev/null 2>&1; then
        echo "User $USER_NAME exists. Adding to group..."
        sudo usermod -aG "$SSH_GROUP" "$USER_NAME"
        echo "User $USER_NAME added to $SSH_GROUP."
    else
        read -p "User $USER_NAME does not exist. Create user? (y/n): " CREATE_USER
        if [[ "$CREATE_USER" == "y" ]]; then
            sudo useradd -m -G "$SSH_GROUP" "$USER_NAME"
            echo "User $USER_NAME created and added to $SSH_GROUP."
        else
            echo "Skipping user creation."
        fi
    fi
    
    read -p "Set/change password for $USER_NAME? (y/n): " SET_PASS
    if [[ "$SET_PASS" == "y" ]]; then
        sudo passwd "$USER_NAME"
    fi
else
    read -p "Do you want to change password for an existing user? (y/n): " CHANGE_PASS
    if [[ "$CHANGE_PASS" == "y" ]]; then
        read -p "Enter username: " USER_NAME
        if id "$USER_NAME" >/dev/null 2>&1; then
            sudo passwd "$USER_NAME"
        else
            echo "User $USER_NAME does not exist."
        fi
    fi
fi

echo "Setup complete."
