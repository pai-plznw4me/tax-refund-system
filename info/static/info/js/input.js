/*
* input 버튼 클릭시 사업장 이름을 가져와 다운로드 버튼 이름을 변경한다.*/
function active_download() {
    var newActionUrl = $('#deduction_info_form').attr('action').replace('index', 'download')
    $('#deduction_info_form').attr('action', newActionUrl)
}


function active_generate() {
       var newActionUrl = $('#deduction_info_form').attr('action').replace('download', 'index')
    $('#deduction_info_form').attr('action', newActionUrl)
}
