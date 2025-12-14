git clone https://github.com/Aum-Patel1234/researchq.git
cd go_ingestion
touch .env

-- copy to env file--

# check go
go version || true
# If not installed, install (Amazon Linux 2)
sudo yum install -y golang
# or on AL2023: sudo dnf install -y golang
go version

cd ~/researchq/go_ingestion

# Build a small static binary (recommended)
# CGO_ENABLED=0 ensures no cgo; adjust GOARCH if needed
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o paper_ingestion ./ 
# Confirm binary created
ls -lh paper_ingestion
file paper_ingestion


sudo useradd -m -s /bin/bash paper || true   # ignore if exists
sudo mkdir -p /opt/paper_ingestion
sudo chown paper:paper /opt/paper_ingestion


# Move .env into /etc and secure it
sudo mv ~/researchq/go_ingestion/.env /etc/paper_ingestion.env
sudo chown root:root /etc/paper_ingestion.env
sudo chmod 600 /etc/paper_ingestion.env
# show the file (for sanity)
sudo sed -n '1,200p' /etc/paper_ingestion.env

# convert 'export VAR=val' to 'VAR=val' (if needed)
sudo sed -i 's/^export //g' /etc/paper_ingestion.env

sudo tee /etc/systemd/system/paper-ingestion.service > /dev/null <<'EOF'
[Unit]
Description=Research Paper Ingestion Service
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/researchq/go_ingestion
ExecStart=/usr/local/bin/paper_ingestion
Restart=on-failure
RestartSec=10
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target


# reload unit files
sudo systemctl daemon-reload

# start the service
sudo systemctl start paper-ingestion

# enable on boot
sudo systemctl enable paper-ingestion

# log status
sudo systemctl status paper-ingestion --no-pager
sudo journalctl -u paper-ingestion -f

# restart

cd ~/researchq/go_ingestion/
sudo chmod +x restart.sh
./restart.sh
sudo journalctl -u paper-ingestion -f --no-pager