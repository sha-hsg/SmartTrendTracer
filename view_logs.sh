#!/bin/bash

# SmartTrendTracer - Log Viewer
# This script helps view and monitor logs from all services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to show menu
show_menu() {
    echo ""
    echo "========================================="
    echo -e "${CYAN}SmartTrendTracer Log Viewer${NC}"
    echo "========================================="
    echo "1)  View Backend API logs"
    echo "2)  View Frontend logs"
    echo "3)  View Tweet Collector logs"
    echo "4)  View Reddit Collector logs"
    echo "5)  View Marker Service logs"
    echo "6)  View MinerU Service logs"
    echo "7)  Tail all logs (live)"
    echo "8)  Search in all logs"
    echo "9)  Show log file sizes"
    echo "10) Clear old logs"
    echo "11) Open logs directory"
    echo "0)  Exit"
    echo "========================================="
}

# Function to view a specific log
view_log() {
    local log_file=$1
    local service_name=$2
    
    if [ -f "$log_file" ]; then
        echo -e "${GREEN}Viewing $service_name logs:${NC}"
        echo "----------------------------------------"
        tail -n 100 "$log_file"
        echo "----------------------------------------"
        echo -e "${YELLOW}Press 'f' to follow live, 'q' to return to menu${NC}"
        read -n 1 -r choice
        if [[ $choice == "f" ]]; then
            tail -f "$log_file"
        fi
    else
        echo -e "${RED}Log file not found: $log_file${NC}"
        echo "Service may not have been started yet."
        read -p "Press Enter to continue..."
    fi
}

# Function to tail all logs
tail_all_logs() {
    echo -e "${GREEN}Following all logs (Ctrl+C to stop):${NC}"
    echo "========================================="
    
    # Build the tail command with all existing log files
    tail_cmd="tail -f"
    
    [ -f "logs/backend.log" ] && tail_cmd="$tail_cmd logs/backend.log"
    [ -f "logs/frontend.log" ] && tail_cmd="$tail_cmd logs/frontend.log"
    [ -f "logs/tweet_collector.log" ] && tail_cmd="$tail_cmd logs/tweet_collector.log"
    [ -f "logs/reddit_collector.log" ] && tail_cmd="$tail_cmd logs/reddit_collector.log"
    [ -f "logs/marker.log" ] && tail_cmd="$tail_cmd logs/marker.log"
    [ -f "logs/mineru.log" ] && tail_cmd="$tail_cmd logs/mineru.log"
    
    if [ "$tail_cmd" == "tail -f" ]; then
        echo -e "${RED}No log files found!${NC}"
        read -p "Press Enter to continue..."
    else
        $tail_cmd
    fi
}

# Function to search in logs
search_logs() {
    echo -e "${CYAN}Enter search term:${NC}"
    read search_term
    
    if [ -z "$search_term" ]; then
        echo -e "${RED}No search term entered${NC}"
        return
    fi
    
    echo -e "${GREEN}Searching for '$search_term' in all logs:${NC}"
    echo "========================================="
    
    for log_file in logs/*.log; do
        if [ -f "$log_file" ]; then
            local basename=$(basename "$log_file")
            local matches=$(grep -c "$search_term" "$log_file" 2>/dev/null)
            if [ "$matches" -gt 0 ]; then
                echo -e "${YELLOW}$basename: $matches matches${NC}"
                echo "----------------------------------------"
                grep --color=always "$search_term" "$log_file" | tail -20
                echo ""
            fi
        fi
    done
    
    read -p "Press Enter to continue..."
}

# Function to show log sizes
show_log_sizes() {
    echo -e "${GREEN}Log File Sizes:${NC}"
    echo "========================================="
    
    if [ -d "logs" ]; then
        ls -lh logs/*.log 2>/dev/null | awk '{print $9 ": " $5}' | sed 's|logs/||g'
        
        echo ""
        echo -e "${CYAN}Total disk usage:${NC}"
        du -sh logs 2>/dev/null
    else
        echo -e "${RED}Logs directory not found${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

# Function to clear old logs
clear_logs() {
    echo -e "${YELLOW}⚠️  Warning: This will delete all log files!${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -d "logs" ]; then
            # Backup current logs with timestamp
            backup_dir="logs_backup_$(date +%Y%m%d_%H%M%S)"
            mkdir -p "$backup_dir"
            cp logs/*.log "$backup_dir/" 2>/dev/null
            
            # Clear log files
            rm -f logs/*.log
            
            echo -e "${GREEN}✓ Logs cleared${NC}"
            echo -e "${CYAN}Backup saved to: $backup_dir${NC}"
        else
            echo -e "${RED}Logs directory not found${NC}"
        fi
    else
        echo "Cancelled"
    fi
    
    read -p "Press Enter to continue..."
}

# Function to open logs directory
open_logs_directory() {
    if [ -d "logs" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            open logs
            echo -e "${GREEN}Opened logs directory in Finder${NC}"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            xdg-open logs 2>/dev/null || echo -e "${YELLOW}Please open 'logs' directory manually${NC}"
        else
            echo -e "${YELLOW}Please open 'logs' directory manually${NC}"
        fi
    else
        echo -e "${RED}Logs directory not found${NC}"
    fi
    
    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    clear
    show_menu
    
    echo -n "Enter choice: "
    read choice
    
    case $choice in
        1)
            view_log "logs/backend.log" "Backend API"
            ;;
        2)
            view_log "logs/frontend.log" "Frontend"
            ;;
        3)
            view_log "logs/tweet_collector.log" "Tweet Collector"
            ;;
        4)
            view_log "logs/reddit_collector.log" "Reddit Collector"
            ;;
        5)
            view_log "logs/marker.log" "Marker Service"
            ;;
        6)
            view_log "logs/mineru.log" "MinerU Service"
            ;;
        7)
            tail_all_logs
            ;;
        8)
            search_logs
            ;;
        9)
            show_log_sizes
            ;;
        10)
            clear_logs
            ;;
        11)
            open_logs_directory
            ;;
        0)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            sleep 1
            ;;
    esac
done