// static/js/app-ocr-list.js

'use strict';

$(function() {
  // Función para actualizar los widgets de estadísticas
  function updateStats(data) {
    const uniqueClients = [...new Set(data.map(item => item.name))].length;
    const totalRecords = data.length;
    const today = moment().format('YYYY-MM-DD');
    const todayRecords = data.filter(item => moment(item.insertion_date).format('YYYY-MM-DD') === today).length;
    const uniqueCategories = [...new Set(data.map(item => item.category))].length;

    $('#totalClients').text(uniqueClients);
    $('#totalRecords').text(totalRecords);
    $('#todayRecords').text(todayRecords);
    $('#categories').text(uniqueCategories);
  }

  // Función para obtener el color de badge basado en la categoría
  function getCategoryBadgeClass(category) {
    const categoryMap = {
      'Documento': 'bg-label-primary',
      'Smarthome': 'bg-label-success',
      'Accessories': 'bg-label-info',
      'Wearables': 'bg-label-warning',
      'Drones': 'bg-label-danger'
    };
    return categoryMap[category] || 'bg-label-secondary';
  }

  let dt_invoice_table = $('.invoice-list-table');

  // Inicialización de DataTable
  if (dt_invoice_table.length) {
    const invoiceTable = dt_invoice_table.DataTable({
      ajax: {
        url: '/api/ocr-records/',
        dataSrc: 'data',
        success: function(response) {
          updateStats(response.data);
        }
      },
      columns: [
        {
          data: null,
          defaultContent: '',
          orderable: false,
          searchable: false
        },
        {
          data: 'numero',
          render: function(data) {
            return `<span class="fw-medium">#${data}</span>`;
          }
        },
        {
          data: null,
          searchable: false,
          orderable: false,
          render: function() {
            return '<i class="ti ti-trending-up text-success me-3"></i>';
          }
        },
        {
          data: 'name',
          render: function(data) {
            return `<h6 class="mb-0">${data}</h6>`;
          }
        },
        {
          data: 'category',
          render: function(data) {
            return `<span class="text-nowrap">${data}</span>`;
          }
        },
        {
          data: 'insertion_date',
          render: function(data) {
            return `<span class="text-nowrap">${moment(data).format('DD MMM YYYY')}</span>`;
          }
        },
        {
          data: 'address',
          render: function(data) {
            return data || '<span class="text-muted">No address</span>';
          }
        },
        {
          data: 'category',
          render: function(data) {
            return `<span class="badge ${getCategoryBadgeClass(data)}">${data}</span>`;
          }
        },
        {
          data: null,
          orderable: false,
          searchable: false,
          render: function(data) {
            return `
              <div class="d-flex align-items-center">
                <a href="javascript:void(0);" 
                   data-bs-toggle="tooltip" 
                   data-bs-placement="top"
                   title="Edit"
                   class="text-body">
                  <i class="ti ti-edit ti-sm me-2"></i>
                </a>
                <a href="javascript:void(0);" 
                   data-bs-toggle="tooltip" 
                   data-bs-placement="top"
                   title="Preview"
                   class="text-body">
                  <i class="ti ti-eye ti-sm me-2"></i>
                </a>
                <a href="javascript:void(0);" 
                   data-bs-toggle="tooltip" 
                   data-bs-placement="top"
                   title="Delete"
                   class="text-body delete-record">
                  <i class="ti ti-trash ti-sm"></i>
                </a>
              </div>
            `;
          }
        }
      ],
      order: [[1, 'desc']],
      dom: '<"row mx-2"<"col-md-2"<"me-3"l>><"col-md-10"<"dt-action-buttons text-xl-end text-lg-start text-md-end text-start d-flex align-items-center justify-content-end flex-md-row flex-column mb-3 mb-md-0"fB>>>t<"row mx-2"<"col-sm-12 col-md-6"i><"col-sm-12 col-md-6"p>>',
      language: {
        sLengthMenu: '_MENU_',
        search: '',
        searchPlaceholder: 'Search Records',
        paginate: {
          previous: '<i class="ti ti-chevron-left ti-sm"></i>',
          next: '<i class="ti ti-chevron-right ti-sm"></i>'
        }
      },
      // Botones de exportación
      buttons: [
        {
          extend: 'collection',
          className: 'btn btn-label-primary dropdown-toggle me-2',
          text: '<i class="ti ti-file-export me-sm-1"></i> <span class="d-none d-sm-inline-block">Export</span>',
          buttons: [
            {
              extend: 'print',
              text: '<i class="ti ti-printer me-1"></i>Print',
              className: 'dropdown-item',
              exportOptions: {
                columns: [1, 3, 4, 5, 6, 7]
              }
            },
            {
              extend: 'csv',
              text: '<i class="ti ti-file-text me-1"></i>CSV',
              className: 'dropdown-item',
              exportOptions: {
                columns: [1, 3, 4, 5, 6, 7]
              }
            },
            {
              extend: 'excel',
              text: '<i class="ti ti-file-spreadsheet me-1"></i>Excel',
              className: 'dropdown-item',
              exportOptions: {
                columns: [1, 3, 4, 5, 6, 7]
              }
            },
            {
              extend: 'pdf',
              text: '<i class="ti ti-file-description me-1"></i>PDF',
              className: 'dropdown-item',
              exportOptions: {
                columns: [1, 3, 4, 5, 6, 7]
              }
            }
          ]
        },
        {
          text: '<i class="ti ti-plus me-sm-1"></i> <span class="d-none d-sm-inline-block">Add New Record</span>',
          className: 'btn btn-primary',
          action: function() {
            window.location.href = '/app/ocr/add/';
          }
        }
      ],
      // Configuración responsive
      responsive: {
        details: {
          display: $.fn.dataTable.Responsive.display.modal({
            header: function(row) {
              const data = row.data();
              return 'Details of Record #' + data.numero;
            }
          }),
          type: 'column',
          renderer: function(api, rowIdx, columns) {
            const data = $.map(columns, function(col, i) {
              return col.title !== '' && col.hidden
                ? '<tr data-dt-row="' +
                    col.rowIndex +
                    '" data-dt-column="' +
                    col.columnIndex +
                    '">' +
                    '<td>' +
                    col.title +
                    ':' +
                    '</td> ' +
                    '<td>' +
                    col.data +
                    '</td>' +
                    '</tr>'
                : '';
            }).join('');

            return data ? $('<table class="table"/><tbody />').append(data) : false;
          }
        }
      },
      initComplete: function() {
        // Inicializar tooltips después de que la tabla se carga
        $('.invoice-list-table [data-bs-toggle="tooltip"]').tooltip();
      }
    });

    // Handle delete record
    $('.invoice-list-table tbody').on('click', '.delete-record', function() {
      const tr = $(this).closest('tr');
      const data = invoiceTable.row(tr).data();
      
      Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, delete it!',
        customClass: {
          confirmButton: 'btn btn-primary me-3',
          cancelButton: 'btn btn-label-secondary'
        },
        buttonsStyling: false
      }).then(function(result) {
        if (result.value) {
          // Aquí irá la lógica de eliminación cuando la implementes
          Swal.fire({
            icon: 'success',
            title: 'Deleted!',
            text: 'Record has been deleted.',
            customClass: {
              confirmButton: 'btn btn-success'
            }
          });
        }
      });
    });
  }
});