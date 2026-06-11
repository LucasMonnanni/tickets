let rowTemplate;

function updateTotalForms() {
    const count = document.querySelectorAll('#personal-tbody tr').length;
    const el = document.getElementById(`id_${PREFIX}-TOTAL_FORMS`);
    if (el) el.value = count;
}

function addEmptyRow() {
    const tbody = document.getElementById('personal-tbody');
    const rowIndex = tbody.querySelectorAll('tr').length;
    let newRowHtml = rowTemplate.split('0').join(String(rowIndex));
    
    const tr = document.createElement('tr');
    tr.innerHTML = newRowHtml;
    tbody.appendChild(tr);
    
    updateTotalForms();
    return tr;
}

function reindexRows() {
    const tbody = document.getElementById('personal-tbody');
    tbody.querySelectorAll('tr').forEach((tr, rowIndex) => {
        tr.querySelectorAll('input').forEach(input => {
            const nameParts = input.name.split('-');
            nameParts[1] = String(rowIndex);
            input.name = nameParts.join('-');
            
            const idParts = input.id.split('-');
            idParts[1] = String(rowIndex);
            input.id = idParts.join('-');
        });
    });
}

function handleDeleteClick(e) {
    const btn = e.target.closest('.delete-btn');
    if (!btn) return;
    
    const tbody = document.getElementById('personal-tbody');
    const rows = tbody.querySelectorAll('tr');
    const tr = btn.closest('tr');
    
    if (rows.length === 1) {
        tr.querySelectorAll('input').forEach(input => input.value = '');
    } else {
        tr.remove();
        reindexRows();
        updateTotalForms();
    }
}

function handleKeydown(e) {
    if (e.key !== 'Enter') return;
    if (!e.target.matches('#personal-tbody input')) return;
    
    e.preventDefault();
    const tr = e.target.closest('tr');
    const field = e.target.name.split('-').pop();
    const nextTr = tr.nextElementSibling;
    
    if (nextTr) {
        const nextInput = nextTr.querySelector(`input[name$="-${field}"]`);
        if (nextInput) nextInput.focus();
    } else {
        addEmptyRow();
        const lastTr = document.querySelector('#personal-tbody tr:last-child');
        const lastInput = lastTr.querySelector(`input[name$="-${field}"]`);
        if (lastInput) lastInput.focus();
    }
}

function handlePaste(e) {
    const table = e.target.closest('#personal-table');
    if (!table) return;

    const pastedData = e.clipboardData.getData('text');
    if (!pastedData.includes('\t') && !pastedData.includes('\n')) return;

    e.preventDefault();

    const fields = ['nombre', 'apellido', 'dni', 'telefono'];
    const targetRow = e.target.closest('tr');
    const targetColumn = e.target.name.split('-').pop();
    const targetColumnIndex = fields.indexOf(targetColumn);
    
    let startRowIndex = 0;
    if (targetRow) {
        startRowIndex = Array.from(document.querySelectorAll('#personal-tbody tr')).indexOf(targetRow);
    }

    const rows = pastedData.split('\n').filter(row => row.trim());
    
    rows.forEach((rowData, rowOffset) => {
        const cols = rowData.split('\t').map(c => c.trim());
        let tr;
        
        const currentRowIndex = startRowIndex + rowOffset;
        const existingRows = document.querySelectorAll('#personal-tbody tr');
        
        if (currentRowIndex < existingRows.length) {
            tr = existingRows[currentRowIndex];
        } else {
            tr = addEmptyRow();
        }

        const inputs = tr.querySelectorAll('input');
        
        cols.forEach((colValue, colOffset) => {
            const fieldIndex = targetColumnIndex + colOffset;
            if (fieldIndex < fields.length && inputs[fieldIndex]) {
                let value = colValue;
                const field = fields[fieldIndex];
                
                if (field === 'dni') {
                    value = value.replace(/[-\s]/g, '');
                } else if (field === 'telefono') {
                    value = value.replace(/[-\s()]/g, '');
                }
                inputs[fieldIndex].value = value;
            }
        });
    });

    reindexRows();
    updateTotalForms();
}

function initAcceso() {
    const tbody = document.getElementById('personal-tbody');
    const table = document.getElementById('personal-table');
    if (!tbody || !table) return;
    
    const firstRow = tbody.querySelector('tr');
    if (firstRow) {
        rowTemplate = firstRow.innerHTML;
    }
    
    table.addEventListener('paste', handlePaste);
    tbody.addEventListener('click', handleDeleteClick);
    document.addEventListener('keydown', handleKeydown);
    
    updateTotalForms();
}

window.initAcceso = initAcceso;
