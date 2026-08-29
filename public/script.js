window.addEventListener("load", () => {
    fetch("/api/getAll", {
        method:"GET"
    })
        .then(r => r.json())
        .then(r => {
            for (const record of r) {
                document.querySelector("table").insertAdjacentHTML("beforeend", `
                    <tr>
                        <a href='https://files.justmore5mins.com/${record.name}'><td>${record.name}</td></a>
                        <td>${record.type}</td>
                        <td>${record.content}</td>
                    </tr>
                `)
            }
        }).catch(r => {
        });

});
