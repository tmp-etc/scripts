#!/bin/bash

MYIP='1.1.1.1'

# firewall shite
ufw --force reset
ufw allow from $MYIP to any port 22 proto tcp
ufw enable
# docker shite
sudo apt remove -y $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1)
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

# install all the shite
sudo apt update
apt-get install -y ranger caca-utils highlight atool w3m poppler-utils mediainfo bat fzf ripgrep docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
# UX shite
adduser --gecos GECOS --disabled-password aaa
while [ ! -d /home/aaa ]
do
    sleep 1
done
echo "alias xforce='mkdir blabla && tar -x -C blabla -f'" >> /home/aaa/.bashrc
echo "export EDITOR=nvim" >> /home/aaa/.bashrc
su -c "ranger --copy-config=all" aaa
sed -i -e 's/^set viewmode miller/set viewmode multipane/g' /home/aaa/.config/ranger/rc.conf
curl -sLO https://github.com/neovim/neovim/releases/latest/download/nvim-linux-x86_64.tar.gz
sudo rm -rf /opt/nvim-linux-x86_64
sudo tar -C /opt -xzf nvim-linux-x86_64.tar.gz
echo 'export PATH="$PATH:/opt/nvim-linux-x86_64/bin"' >> /home/aaa/.bashrc
mkdir /home/aaa/.config/nvim
chown -R aaa:aaa /home/aaa/.config/nvim
cat > /home/aaa/.config/nvim/init.lua << 'EOF'
vim.pack.add({
  { src = 'https://github.com/nvim-tree/nvim-tree.lua' },
  { src = "https://github.com/junegunn/fzf" },
  { src = "https://github.com/junegunn/fzf.vim" }
})

-- disable netrw at the very start of your init.lua
vim.g.loaded_netrw = 1
vim.g.loaded_netrwPlugin = 1

-- optionally enable 24-bit colour
vim.opt.termguicolors = true

---@type nvim_tree.config
local config = {
  sort = {
    sorter = "case_sensitive",
  },
  view = {
    width = 30,
  },
  renderer = {
    group_empty = true,
    icons = {
      show = {
        git = false,
        folder = false,
        file = false,
        folder_arrow = false,
      }
    },
    indent_markers = {
      enable = true,
      icons = { corner = "└", edge = "│", item = "├", bottom = "─", none = " " },
    }
  },
  filters = {
    dotfiles = true,
  }
}
require("nvim-tree").setup(config)

--vim.api.nvim_create_autocmd("VimEnter", {
--  callback = function() require("nvim-tree.api").tree.open() end,
--})

vim.keymap.set("n", "<C-n>", ":NvimTreeToggle<CR>")
vim.opt.wrap = false
EOF

echo "alias vim='nvim'" >> /home/aaa/.bashrc
# --- keymaps for nvim ---
## Ctrl+n - toggle file explorer
## Ctrl+v - vsplit
## Ctrl+6 - previous buffer/file
## f - filter
## F - clear filter
## E - expand all
## W - collapse all
