$("#data").on("change", function() {
    $(".sez-orari, .riga-pulsante-prenota, .errore-nessun-orario").addClass("d-none");
    var dataSelezionata = $(this).val();
    $.ajax({
        url: "/ajax/orari_disponibili",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ "data": dataSelezionata }),
        success: function(response) {
            console.log(response);

            // Nascondi tutti gli orari inizialmente
            $(".input-orario, .label-orario").hide();

            if (response.length > 0){
                // Mostra solo gli orari disponibili in base alla risposta
                response.forEach(function(orario) {
                    $(`#orario-${orario.id}`).show();  // Mostra input
                    $(`label[for="orario-${orario.id}"]`).show();  // Mostra label corrispondente
                });
                $(".sez-orari, .riga-pulsante-prenota").removeClass("d-none");
            }else{
                $(".errore-nessun-orario").removeClass("d-none");
            }

        },
        error: function(error) {
            console.log("Errore durante il recupero degli orari disponibili.");
            console.log(error);
        }
    });
});

