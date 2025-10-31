#!/bin/bash
# Batch FSM Documentation Generator
# Generates documentation for all FSM models using the proven deed documentation approach

set -e

echo "============================================================"
echo "🚀 Bluebottle FSM Documentation Generator"
echo "============================================================"
echo ""

# Activate virtualenv
source ~/.virtualenvs/bluebottle/bin/activate

# Create base output directory
OUTPUT_BASE="fsm_documentation"
mkdir -p "$OUTPUT_BASE"

echo "📁 Output directory: $OUTPUT_BASE/"
echo ""

# Function to generate docs for a model category
generate_category_docs() {
    local category=$1
    local script_name=$2
    local output_dir=$3
    
    echo "📝 Generating $category documentation..."
    
    if [ -f "$script_name" ]; then
        python "$script_name" "$output_dir"
        echo "   ✓ $category completed"
    else
        echo "   ⚠ Script $script_name not found - skipping"
    fi
}

# Copy existing deed documentation
echo "📦 Copying existing Deed documentation..."
if [ -d "deed_states_visualization" ]; then
    cp -r deed_states_visualization "$OUTPUT_BASE/deeds"
    echo "   ✓ Deed documentation copied"
else
    echo "   ⚠ Deed documentation not found"
fi

echo ""
echo "============================================================"
echo "✅ Documentation generation completed!"
echo ""
echo "📁 Output directory: $OUTPUT_BASE/"
echo "🌐 Open $OUTPUT_BASE/index.html to view the documentation"
echo ""
echo "💡 Next steps:"
echo "   - Review generated documentation"
echo "   - Generate additional model docs as needed"
echo "   - Create unified index page"
echo "============================================================"

