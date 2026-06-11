const criteria = [
    ['{}', '='],            //0
    ['not__{}', '≠'],       
    ['{}__icontains', '⊃'], //2
    ['{}__lte', '≤'],       
    ['{}__gte', '≥'],       //4
    ['{}__isnull', '=∅']
]

String.prototype.format = function (str) {
    return this.replace('{}', str);
};

String.prototype.unformat = function () {
    if (fields.hasOwnProperty(this)) {
        return [this, 0]
    }
    for (let i = 1; i<criteria.length; i++) {
        let re = new RegExp(criteria[i][0].format('\w*'))
        let res = this.match(re)
        if (!res) {continue} 
        res = this.replace(res[0], '')
        if (fields.hasOwnProperty(res)) {
            return [res, i]
        }
    }
    return ['', -1]
}

const criteriaIdcs = {
    'ref': [0, 1],
    'bool': [0],
    'string': [0, 2],
    'numero': [0, 3, 4],
}

let fields = {};
let filterCount = -1;
let filterButton;
let columnNames = [];
let visibleColumns = [];

function setOrder(field) {
    let url = new URL(document.location.href)
    if (url.searchParams.get('order') == field) {field = '-'+field}
    url.searchParams.set('order', field)
    window.location = url.href
}

function goToList() {
    let url = new URL(document.location.href)
    url.pathname = url.pathname.split('/').filter((value)=>{return value != 'mapa'}).join('/')
    window.location = url.href
}

function goToMap() {
    let url = new URL(document.location.href)
    url.pathname += 'mapa/'
    window.location = url.href
}

function setUpFields() {
    fields = JSON.parse(document.getElementById('fields-data').textContent)

    let addFilterDiv = document.querySelector('#filtrosButtons')
    let btn = document.createElement('button')
    btn.type = 'button'
    btn.className = 'btn btn-secondary mx-1'
    btn.dataset.bsToggle = 'dropdown'
    btn.ariaExpanded = 'false'
    btn.innerHTML = '<span class="fs-5"><i class="bi bi-funnel"></i></span><span style="font-size:0.7rem; margin-left:-0.5rem"><i class="bi bi-plus "></i></span>'
    addFilterDiv.appendChild(btn)
    let ul = document.createElement('ul')
    ul.className = 'dropdown-menu'
    for (let field in fields) {
        if (fields.hasOwnProperty(field)) {
            // Create the option
            let li = document.createElement('li')
            let a = document.createElement('a')
            a.textContent = fields[field].nombre;
            a.className = 'dropdown-item'
            a.addEventListener('click', ()=>{addFilter(field)})
            li.appendChild(a)
            ul.appendChild(li)
        }
    }
    addFilterDiv.appendChild(ul)
    document.querySelectorAll(".page_link").forEach(function(element){
        let url = new URL(document.location.href)
        url.searchParams.set('page', element.dataset.page)
        element.href = url.href
    })
    filterCount = 0;
    filterButton = document.createElement('a')
    filterButton.className = 'btn btn-secondary mx-1';
    filterButton.innerHTML = 'Filtrar'
    filterButton.addEventListener('click', sendFilters)
}

function createFilterCard(field) {
    if (filterCount < 0) {console.log('Algo está mal.')}
    let filterId = ++filterCount;
    // Create the col div
    var card = document.createElement('div');
    card.className = 'col-xl-4 col-md-6 px-2 custom-card g-2';

    // Create the input div
    var group = document.createElement('div');
    group.className = 'input-group';
    card.appendChild(group);
    
    // Create the field label
    var label = document.createElement('span');
    label.className = 'input-group-text';
    label.innerHTML = fields[field].nombre;
    group.appendChild(label)
    
    // Create the dropdown select for criterion
    var select = document.createElement('select');
    select.className = 'btn btn-outline-secondary criterion';
    //select.style.width = '3rem'
    group.appendChild(select);

    // Populate dropdown with criteria
    let fieldCriteria = criteriaIdcs[fields[field].tipo]
    if (fieldCriteria) {
        for (let idx of fieldCriteria) {
            let c = criteria[idx]
            let option = document.createElement('option');
            option.textContent = c[1];
            option.value = c[0].format(field);
            select.appendChild(option);
        }
    }
    
    // Create the datalist
    var datalist = document.createElement('datalist');
    datalist.id = 'values-'+filterId;
    group.appendChild(datalist);
    
    // Populate the datalist with the selected field's values
    fields[field].valores.forEach(function(value) {
        var option = document.createElement('option');
        option.value = value;
        datalist.appendChild(option);
    });

    // Create the input field
    var input = document.createElement('input');
    input.className = 'form-control';
    input.setAttribute('list', 'values-'+filterId);
    input.setAttribute('type', 'text');
    input.setAttribute('placeholder', '...');
    group.appendChild(input);

    var close = document.createElement('span');
    close.className = 'input-group-text';
    close.innerHTML = 'X';
    close.addEventListener('click', () => {
        card.remove();
        sendFilters();
    });
    group.appendChild(close)
    
    // Append the card to the body (or wherever you want to add it)
    document.querySelector('#filtros').append(card);
    if (filterCount == 1) {
        document.querySelector('#filtrosButtons').append(filterButton)
    }
    return card;
}

function escapeUnicode(str) {
    return encodeURIComponent(str)
}

function unescapeUnicode(str) {
    return decodeURIComponent(JSON.parse('"' + str.replace(/\"/g, '\\"') + '"'))
}

function loadFilters() {
    let url = new URL(window.location.href)
    let keys = new Set(url.searchParams.keys())
    for (let key of keys) {
        if (!(key=='order' || key=='page')) {
            let rawKey = unescapeUnicode(key)
            let [field, criterion] = rawKey.unformat()
            if (criterion == -1) { continue; }
            let values = url.searchParams.getAll(key)
            for (value of values) {
                let card = createFilterCard(field)
                card.querySelector('select.criterion').value = criteria[criterion][0].format(field)
                card.querySelector('input').value = unescapeUnicode(value)
            }
        }
    }
}

function addFilter(field) {
    let filtros = document.querySelector('#filtros');
    createFilterCard(field);
}

function sendFilters() {
    let url = new URL(window.location.href)
    url.searchParams.sort()
    let newSearchParams = new URLSearchParams()

    let filtros = document.querySelector('#filtros')
    let count = filtros.childElementCount
    for (let i = 0; i < count; i++) {
        let child = filtros.children[i]
        let key = child.querySelector('select.criterion').value
        let value = escapeUnicode(child.querySelector('input').value)
        if (value) {
            newSearchParams.append(key, value);
        }
    }
    newSearchParams.sort()
    if (newSearchParams.toString() != url.searchParams.toString()) {
        window.location = url.protocol + '//' + url.host + url.pathname + '?' + newSearchParams.toString()
    }
}

function hideColumn(index) {
    document.querySelectorAll(`th:nth-child(${index+1}), td:nth-child(${index+1})`).forEach((node)=>{node.classList.add('d-none')})
    visibleColumns[index] = 0
    document.querySelector(`#add-column-dropdown li:nth-child(${index+1}) a`).classList.remove('disabled')
    sessionStorage.setItem(`visible-${model}-columns`, JSON.stringify(visibleColumns))
}

function showColumn(index) {
    document.querySelectorAll(`th:nth-child(${index+1}), td:nth-child(${index+1})`).forEach((node)=>{node.classList.remove('d-none')})
    visibleColumns[index] = 1
    sessionStorage.setItem(`visible-${model}-columns`, JSON.stringify(visibleColumns))
}

function displayTable() {
    visibleColumns = JSON.parse(sessionStorage.getItem(`visible-${model}-columns`)) || defaultVisibleColumns
    let addColumnHeader = document.createElement('th')
    document.querySelector('thead > tr').appendChild(addColumnHeader)
    let btn = document.createElement('div') 
    btn.type = 'button'
    btn.className = 'mx-1'
    btn.dataset.bsToggle = 'dropdown'
    btn.ariaExpanded = 'false'
    btn.innerHTML = '<span ><i class="bi bi-plus-circle"></i></span>'
    let ul = document.createElement('ul')
    ul.id = 'add-column-dropdown'
    ul.className = 'dropdown-menu'
    addColumnHeader.appendChild(btn)
    addColumnHeader.appendChild(ul)

    for (let i = 0; i<visibleColumns.length; i++) {
        let header = document.querySelector(`th:nth-child(${i+1})`)
        columnNames[i] = header.textContent
        let li = document.createElement('li')
        let a = document.createElement('a')
        a.textContent = columnNames[i];
        a.className = 'dropdown-item'
        a.addEventListener('click', (event)=>{showColumn(i); event.target.classList.add('disabled')})
        li.appendChild(a)
        ul.appendChild(li)
        if (visibleColumns[i]) { 
            a.classList.add('disabled')
        } else {
            document.querySelectorAll(`th:nth-child(${i+1}), td:nth-child(${i+1})`).forEach((node)=>{node.classList.add('d-none')})
        }
        if (header.classList.contains('removable')) {
            header.addEventListener('mouseenter', ()=>{
                let timeout = setTimeout(()=> {
                    onHeaderHover(header)
                    timeout = false
                }, 1000)
                header.addEventListener('mouseleave', ()=>{onHeaderExit(header, timeout)}, { once: true });
            });
        } else {
            li.style.display = 'none'
        }
    }    
}

function onHeaderHover(header) {
    let delBadge = document.createElement('span')
    delBadge.classList.add('temporary', 'position-absolute', 'top-0', 'end-0')
    let delButton = document.createElement('i')
    delButton.classList.add('bi', 'bi-x-circle', 'text-end')
    delButton.style += 'position:fixed; z-index:10'
    delButton.addEventListener('click', (event)=> {
        event.stopPropagation();
        hideColumn(header.cellIndex)
    })
    header.appendChild(delBadge)
    delBadge.appendChild(delButton)
}

function onHeaderExit(header, timeout) {
    if (timeout) {
        window.clearTimeout(timeout)
    } else {
        header.querySelector('.temporary').remove()
    }
}

document.addEventListener('DOMContentLoaded',  () => {
    setUpFields();
    loadFilters();
    displayTable();
})