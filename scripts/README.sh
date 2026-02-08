#!/bin/bash
# 🔧 Scripts Directory

# Available scripts:

echo "✅ Available scripts:"
echo ""
ls -1 *.sh | while read script; do
    echo "  • $script"
done
echo ""
echo "Usage:"
echo "  bash scripts/script_name.sh"
echo ""
echo "For help on any script:"
echo "  bash scripts/script_name.sh --help"
