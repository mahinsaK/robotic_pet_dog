# Dynamic DNS Setup Guide

## Using Dynamic DNS (DDNS) for Global Access

### What is DDNS?
Dynamic DNS automatically updates your domain name to point to your current IP address, even when it changes.

### Popular Free DDNS Providers:
1. **No-IP.com** - Free subdomain (yourname.ddns.net)
2. **DuckDNS.org** - Free, simple setup
3. **Dynu.com** - Free with multiple domains
4. **FreeDNS.afraid.org** - Many domain options

### Setup Example with DuckDNS:

#### Step 1: Register Domain
1. Go to https://www.duckdns.org/
2. Sign in with Google/GitHub
3. Create subdomain: `yourrobot.duckdns.org`
4. Note your token

#### Step 2: Install Duck DNS Client on Pi
```bash
# Create directory
mkdir /home/ubuntu/duckdns
cd /home/ubuntu/duckdns

# Create update script
echo 'echo url="https://www.duckdns.org/update?domains=yourrobot&token=YOUR_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -' > duck.sh
chmod 700 duck.sh

# Test update
./duck.sh

# Add to crontab for auto-update every 5 minutes
crontab -e
# Add line: */5 * * * * /home/ubuntu/duckdns/duck.sh >/dev/null 2>&1
```

#### Step 3: Router Port Forwarding
1. Access router admin (usually 192.168.1.1 or 192.168.0.1)
2. Find "Port Forwarding" or "Virtual Server"
3. Forward port 8765 to Pi's local IP
4. Save settings

#### Step 4: Update Robot/App URLs
- Robot: `RELAY_URL = "ws://yourrobot.duckdns.org:8765"`
- Mobile: `value="ws://yourrobot.duckdns.org:8765"`

### Security Considerations:
- Enable router firewall
- Use strong passwords
- Consider VPN for additional security
- Monitor access logs

### Testing:
```bash
# Test external access
curl -I http://yourrobot.duckdns.org:8765
```

## Alternative: Tailscale VPN (Easiest!)
1. Install Tailscale on Pi and your devices
2. Access via Tailscale IP (100.x.x.x)
3. No port forwarding needed
4. Secure by default
