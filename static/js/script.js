// Invoice OCR Analysis Frontend JavaScript

// Global variables
let currentFile = null;
let analysisResults = null;

// DOM elements
const uploadSection = document.getElementById('uploadSection');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const selectedFile = document.getElementById('selectedFile');
const fileName = document.getElementById('fileName');
const uploadBtn = document.getElementById('uploadBtn');

// New elements for "Analyze Another File"
const anotherFileForm = document.getElementById('anotherFileForm');
const anotherFileInput = document.getElementById('anotherFileInput');
const anotherSelectedFile = document.getElementById('anotherSelectedFile');
const anotherFileName = document.getElementById('anotherFileName');
const anotherUploadBtn = document.getElementById('anotherUploadBtn');

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
});

function setupEventListeners() {
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Form submission
    uploadForm.addEventListener('submit', handleFormSubmit);
    
    // Another file input change
    anotherFileInput.addEventListener('change', handleAnotherFileSelect);
    
    // Another form submission
    anotherFileForm.addEventListener('submit', handleAnotherFormSubmit);
}

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        currentFile = file;
        showSelectedFile(file.name);
        uploadBtn.disabled = false;
    } else {
        currentFile = null;
        hideSelectedFile();
        uploadBtn.disabled = true;
    }
}

// Show selected file
function showSelectedFile(name) {
    fileName.textContent = name;
    selectedFile.style.display = 'flex';
}

// Hide selected file
function hideSelectedFile() {
    selectedFile.style.display = 'none';
    fileName.textContent = '';
}

// Remove selected file
function removeFile() {
    fileInput.value = '';
    currentFile = null;
    hideSelectedFile();
    uploadBtn.disabled = true;
}

// Handle another file selection
function handleAnotherFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        currentFile = file;
        showAnotherSelectedFile(file.name);
        anotherUploadBtn.disabled = false;
    } else {
        currentFile = null;
        hideAnotherSelectedFile();
        anotherUploadBtn.disabled = true;
    }
}

// Show another selected file
function showAnotherSelectedFile(name) {
    anotherFileName.textContent = name;
    anotherSelectedFile.style.display = 'flex';
}

// Hide another selected file
function hideAnotherSelectedFile() {
    anotherSelectedFile.style.display = 'none';
    anotherFileName.textContent = '';
}

// Remove another selected file
function removeAnotherFile() {
    anotherFileInput.value = '';
    currentFile = null;
    hideAnotherSelectedFile();
    anotherUploadBtn.disabled = true;
}

// Handle form submission
async function handleFormSubmit(event) {
    event.preventDefault();
    
    if (!currentFile) {
        showError('Please select a file to upload.');
        return;
    }
    
    // Show loading state
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', currentFile);
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.error) {
            showError(result.error);
        } else if (result.success) {
            analysisResults = result;
            showResults(result);
        } else {
            showError('Unknown error occurred during analysis.');
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        showError('Network error occurred. Please try again.');
    }
}

// Handle another form submission
async function handleAnotherFormSubmit(event) {
    event.preventDefault();
    
    if (!currentFile) {
        showError('Please select a file to upload.');
        return;
    }
    
    // Show loading state
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', currentFile);
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.error) {
            showError(result.error);
        } else if (result.success) {
            analysisResults = result;
            showResults(result);
        } else {
            showError('Unknown error occurred during analysis.');
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        showError('Network error occurred. Please try again.');
    }
}

// Show loading state
function showLoading() {
    uploadSection.style.display = 'none';
    loadingSection.style.display = 'block';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Simulate loading steps
    simulateLoadingSteps();
}

// Simulate loading steps
function simulateLoadingSteps() {
    const steps = document.querySelectorAll('.loading-steps .step');
    let currentStep = 0;
    
    const stepInterval = setInterval(() => {
        if (currentStep > 0) {
            steps[currentStep - 1].classList.remove('active');
        }
        
        if (currentStep < steps.length) {
            steps[currentStep].classList.add('active');
            currentStep++;
        } else {
            clearInterval(stepInterval);
        }
    }, 800);
}

// Show results
function showResults(data) {
    uploadSection.style.display = 'none';
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'block';
    errorSection.style.display = 'none';
    
    // Populate summary cards
    populateSummaryCards(data.summary);
    
    // Populate overall status
    populateOverallStatus(data.summary);
    
    // Populate tax summary
    populateTaxSummary(data.tax_summary);
    
    // Populate invoice items table
    populateInvoiceItemsTable(data.invoice_items);
    
    // Populate detailed analysis
    populateDetailedAnalysis(data.invoice_items);
    
    // Populate extracted text
    populateExtractedText(data.extracted_text);
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Populate summary cards
function populateSummaryCards(summary) {
    document.getElementById('totalItems').textContent = summary.total_items;
    document.getElementById('matchedItems').textContent = summary.matched_items;
    document.getElementById('matchPercentage').textContent = `${summary.match_percentage.toFixed(1)}%`;
    document.getElementById('totalValue').textContent = `₹${summary.total_invoice_value.toFixed(2)}`;
}

// Populate overall status
function populateOverallStatus(summary) {
    const statusBadge = document.getElementById('statusBadge');
    const statusText = document.getElementById('statusText');
    
    statusText.textContent = summary.overall_status;
    
    // Remove existing classes
    statusBadge.className = 'status-badge';
    
    // Add appropriate class based on status
    if (summary.overall_status.includes('EXCELLENT')) {
        statusBadge.classList.add('excellent');
    } else if (summary.overall_status.includes('GOOD')) {
        statusBadge.classList.add('good');
    } else if (summary.overall_status.includes('ATTENTION')) {
        statusBadge.classList.add('attention');
    } else if (summary.overall_status.includes('POOR')) {
        statusBadge.classList.add('poor');
    }
}

// Populate tax summary
function populateTaxSummary(taxSummary) {
    const taxGrid = document.getElementById('taxGrid');
    const taxSummarySection = document.getElementById('taxSummary');
    
    if (Object.keys(taxSummary).length === 0) {
        taxSummarySection.style.display = 'none';
        return;
    }
    
    taxSummarySection.style.display = 'block';
    taxGrid.innerHTML = '';
    
    Object.entries(taxSummary).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
            const taxItem = document.createElement('div');
            taxItem.className = 'tax-item';
            
            const label = formatTaxLabel(key);
            const formattedValue = formatTaxValue(key, value);
            
            taxItem.innerHTML = `
                <div class="tax-label">${label}</div>
                <div class="tax-value">${formattedValue}</div>
            `;
            
            taxGrid.appendChild(taxItem);
        }
    });
}

// Format tax label
function formatTaxLabel(key) {
    const labels = {
        'igst_amount': 'IGST Amount',
        'output_igst': 'Output IGST',
        'gst_rate': 'GST Rate',
        'cgst': 'CGST',
        'sgst': 'SGST',
        'sub_total': 'Sub Total',
        'courier_charges': 'Courier Charges',
        'add_charges': 'Additional Charges',
        'taxable_value': 'Taxable Value',
        'tcs_amount': 'TCS Amount',
        'cgst_amount': 'CGST Amount',
        'sgst_amount': 'SGST Amount',
        'total_inc_taxes': 'Total Inc. Taxes'
    };
    
    return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Format tax value
function formatTaxValue(key, value) {
    if (key === 'gst_rate') {
        return `${value}%`;
    } else {
        return `₹${parseFloat(value).toFixed(2)}`;
    }
}

// Populate invoice items table
function populateInvoiceItemsTable(items) {
    const tbody = document.getElementById('itemsTableBody');
    tbody.innerHTML = '';
    
    items.forEach(item => {
        const row = document.createElement('tr');
        
        const materialName = document.createElement('td');
        materialName.textContent = item.material_name;
        materialName.title = item.material_name;
        
        const quantity = document.createElement('td');
        quantity.textContent = item.quantity ? item.quantity.toFixed(2) : '—';
        
        const rate = document.createElement('td');
        rate.textContent = item.rate ? `₹${item.rate.toFixed(2)}` : '—';
        
        const amount = document.createElement('td');
        amount.textContent = `₹${item.amount.toFixed(2)}`;
        
        const databaseMatch = document.createElement('td');
        if (item.csv_match) {
            databaseMatch.innerHTML = `
                <div><strong>${item.csv_match.database_name}</strong></div>
                <div style="font-size: 0.8em; color: #666;">
                    Supplier: ${item.csv_match.database_supplier}<br>
                    Price: ₹${item.csv_match.database_price.toFixed(2)}<br>
                    Method: ${item.csv_match.match_method}<br>
                    Score: ${item.csv_match.confidence_score.toFixed(1)}%
                </div>
            `;
        } else {
            databaseMatch.innerHTML = '<span style="color: #e53e3e;">❌ No Match</span>';
        }
        
        const priceAnalysis = document.createElement('td');
        if (item.price_analysis) {
            const diffClass = getPriceDifferenceClass(item.price_analysis.difference_percentage);
            priceAnalysis.innerHTML = `
                <div><strong>Invoice:</strong> ₹${item.price_analysis.invoice_rate.toFixed(2)}</div>
                <div><strong>Database:</strong> ₹${item.price_analysis.database_price.toFixed(2)}</div>
                <div class="${diffClass}">
                    <strong>Diff:</strong> ₹${item.price_analysis.difference.toFixed(2)} 
                    (${item.price_analysis.difference_percentage.toFixed(1)}%)
                </div>
                <div style="font-size: 0.8em; margin-top: 0.5em;">
                    ${item.price_analysis.price_status}
                </div>
            `;
        } else {
            priceAnalysis.textContent = '—';
        }
        
        const status = document.createElement('td');
        const statusClass = getStatusClass(item.status);
        status.innerHTML = `<span class="status-badge-table ${statusClass}">${item.status}</span>`;
        
        row.appendChild(materialName);
        row.appendChild(quantity);
        row.appendChild(rate);
        row.appendChild(amount);
        row.appendChild(databaseMatch);
        row.appendChild(priceAnalysis);
        row.appendChild(status);
        
        tbody.appendChild(row);
    });
}

// Get price difference class
function getPriceDifferenceClass(percentage) {
    if (percentage === 0) return 'exact';
    if (percentage <= 2) return 'minor';
    if (percentage <= 5) return 'small';
    if (percentage <= 10) return 'moderate';
    if (percentage <= 25) return 'significant';
    return 'major';
}

// Get status class
function getStatusClass(status) {
    if (status.includes('EXACT')) return 'exact';
    if (status.includes('MINOR')) return 'minor';
    if (status.includes('SMALL')) return 'small';
    if (status.includes('MODERATE')) return 'moderate';
    if (status.includes('SIGNIFICANT')) return 'significant';
    if (status.includes('MAJOR')) return 'major';
    if (status.includes('NOT MATCHED')) return 'not-matched';
    return 'not-matched';
}

// Populate detailed analysis
function populateDetailedAnalysis(items) {
    const detailedAnalysis = document.getElementById('detailedAnalysis');
    
    // Group items by price match status
    const exactMatches = [];
    const minorDifferences = [];
    const priceMismatches = [];
    
    items.forEach(item => {
        if (item.price_analysis) {
            if (item.price_analysis.difference_percentage === 0) {
                exactMatches.push(item);
            } else if (item.price_analysis.difference_percentage <= 2) {
                minorDifferences.push(item);
            } else {
                priceMismatches.push(item);
            }
        }
    });
    
    let html = '<h3><i class="fas fa-chart-bar"></i> Price Analysis Summary</h3>';
    
    // Exact matches
    if (exactMatches.length > 0) {
        html += `
            <div class="analysis-group">
                <h4 style="color: #38a169; margin-bottom: 1rem;">
                    ✅ Items with Exact Price Match (${exactMatches.length})
                </h4>
                <div class="analysis-items">
        `;
        exactMatches.forEach(item => {
            html += `
                <div class="analysis-item exact">
                    <strong>${item.material_name}</strong> - 
                    Invoice: ₹${item.price_analysis.invoice_rate.toFixed(2)} | 
                    Database: ₹${item.price_analysis.database_price.toFixed(2)} | 
                    Status: ✅ PERFECT MATCH
                </div>
            `;
        });
        html += '</div></div>';
    }
    
    // Minor differences
    if (minorDifferences.length > 0) {
        html += `
            <div class="analysis-group">
                <h4 style="color: #d69e2e; margin-bottom: 1rem;">
                    🟡 Items with Minor Price Differences (${minorDifferences.length})
                </h4>
                <div class="analysis-items">
        `;
        minorDifferences.forEach(item => {
            html += `
                <div class="analysis-item minor">
                    <strong>${item.material_name}</strong> - 
                    Invoice: ₹${item.price_analysis.invoice_rate.toFixed(2)} | 
                    Database: ₹${item.price_analysis.database_price.toFixed(2)} | 
                    Diff: ₹${item.price_analysis.difference.toFixed(2)} 
                    (${item.price_analysis.difference_percentage.toFixed(1)}%) | 
                    Status: ⚠️ MINOR DIFFERENCE
                </div>
            `;
        });
        html += '</div></div>';
    }
    
    // Price mismatches
    if (priceMismatches.length > 0) {
        html += `
            <div class="analysis-group">
                <h4 style="color: #e53e3e; margin-bottom: 1rem;">
                    🔴 ITEMS WITH PRICE MISMATCHES (${priceMismatches.length})
                </h4>
                <div style="background: #fed7d7; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                    ⚠️ THESE PRICES DON'T MATCH THE DATABASE!
                </div>
                <div class="analysis-items">
        `;
        priceMismatches.forEach(item => {
            const severity = getSeverity(item.price_analysis.difference_percentage);
            const severityIcon = severity === 'HIGH' ? '🔴' : severity === 'MEDIUM' ? '🟡' : '🟢';
            
            html += `
                <div class="analysis-item mismatch ${severity.toLowerCase()}">
                    ${severityIcon} <strong>${item.material_name}</strong> - 
                    Invoice: ₹${item.price_analysis.invoice_rate.toFixed(2)} | 
                    Database: ₹${item.price_analysis.database_price.toFixed(2)} | 
                    Diff: ₹${item.price_analysis.difference.toFixed(2)} 
                    (${item.price_analysis.difference_percentage.toFixed(1)}%) | 
                    Status: ❌ PRICE DOESN'T MATCH | 
                    Severity: ${severity}
                </div>
            `;
        });
        html += '</div></div>';
    }
    
    // Summary
    const totalItems = items.length;
    const totalMismatches = minorDifferences.length + priceMismatches.length;
    
    html += `
        <div class="analysis-summary">
            <h4 style="margin-bottom: 1rem;">📊 Price Match Summary</h4>
            <div class="summary-stats">
                <div class="stat-item">
                    <strong>Exact Matches:</strong> ${exactMatches.length}
                </div>
                <div class="stat-item">
                    <strong>Minor Differences (0-2%):</strong> ${minorDifferences.length}
                </div>
                <div class="stat-item">
                    <strong>Significant Mismatches (>2%):</strong> ${priceMismatches.length}
                </div>
                <div class="stat-item">
                    <strong>Total Items with Price Differences:</strong> ${totalMismatches}
                </div>
            </div>
        </div>
    `;
    
    detailedAnalysis.innerHTML = html;
}

// Get severity level
function getSeverity(percentage) {
    if (percentage > 10) return 'HIGH';
    if (percentage > 5) return 'MEDIUM';
    return 'LOW';
}

// Populate extracted text
function populateExtractedText(text) {
    document.getElementById('extractedText').textContent = text;
}

// Toggle extracted text
function toggleExtractedText() {
    const content = document.getElementById('extractedTextContent');
    const icon = document.getElementById('extractedTextIcon');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        icon.style.transform = 'rotate(0deg)';
    }
}

// Show error
function showError(message) {
    uploadSection.style.display = 'none';
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'block';
    
    document.getElementById('errorMessage').textContent = message;
}

// Reset form
function resetForm() {
    uploadSection.style.display = 'block';
    loadingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Reset main form
    uploadForm.reset();
    removeFile();
    
    // Reset another file form
    anotherFileForm.reset();
    removeAnotherFile();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Add some CSS for the analysis groups
const style = document.createElement('style');
style.textContent = `
    .analysis-group {
        margin-bottom: 2rem;
        padding: 1.5rem;
        background: #f7fafc;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    
    .analysis-items {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    
    .analysis-item {
        padding: 1rem;
        background: white;
        border-radius: 8px;
        border-left: 4px solid #e2e8f0;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    
    .analysis-item.exact {
        border-left-color: #48bb78;
        background: #f0fff4;
    }
    
    .analysis-item.minor {
        border-left-color: #ed8936;
        background: #fffbeb;
    }
    
    .analysis-item.mismatch {
        border-left-color: #f56565;
        background: #fff5f5;
    }
    
    .analysis-item.mismatch.high {
        border-left-color: #e53e3e;
        background: #fed7d7;
    }
    
    .analysis-item.mismatch.medium {
        border-left-color: #dd6b20;
        background: #fed7d7;
    }
    
    .analysis-item.mismatch.low {
        border-left-color: #f56565;
        background: #fed7d7;
    }
    
    .analysis-summary {
        margin-top: 2rem;
        padding: 1.5rem;
        background: #edf2f7;
        border-radius: 10px;
    }
    
    .summary-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
    }
    
    .stat-item {
        padding: 0.75rem;
        background: white;
        border-radius: 8px;
        font-size: 0.9rem;
    }
    
    .exact { color: #22543d; }
    .minor { color: #744210; }
    .mismatch { color: #742a2a; }
`;
document.head.appendChild(style);
