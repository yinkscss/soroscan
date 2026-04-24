django.jQuery(function($) {
    const contractSelect = $('#id_contract');
    const eventTypeInput = $('#id_event_type');
    
    // Convert to a datalist
    const datalistId = 'event_type_list';
    eventTypeInput.attr('list', datalistId);
    if ($('#' + datalistId).length === 0) {
        eventTypeInput.after('<datalist id="' + datalistId + '"></datalist>');
    }
    
    function updateEventTypes() {
        const contractId = contractSelect.val();
        const datalist = $('#' + datalistId);
        datalist.empty();
        
        if (contractId) {
            $.getJSON('/admin/ingest/webhooksubscription/event-types/?contract_id=' + contractId, function(data) {
                if (data.results) {
                    data.results.forEach(function(item) {
                        datalist.append($('<option>', {value: item.id}));
                    });
                }
            });
        }
    }
    
    contractSelect.on('change', updateEventTypes);
    // run on load
    updateEventTypes();
});
