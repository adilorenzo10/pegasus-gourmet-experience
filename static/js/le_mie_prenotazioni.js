$(".cancella-prenotazione").on("click", function() {
    if(confirm("Sei sicuro di voler cancellare la prenotazione selezionata?\n L'operazione è irreversibile.")){
        var id_prenotazione = $(this).data("id_prenotazione");
        $.ajax({
            url: "/ajax/cancella_prenotazione",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ "id_prenotazione": id_prenotazione }),
            success: function(response) {
                console.log(response.message);
                if (response.success){
                    // Se l'operazione ha successo, rimuovi il div con data-id corrispondente
                    $("div.prenotazione[data-id='" + id_prenotazione + "']").remove();
                }
            },
            error: function(error) {
                console.log("Errore durante la cancellazione della prenotazione.");
                console.log(error);
            }
        });
    }
});


